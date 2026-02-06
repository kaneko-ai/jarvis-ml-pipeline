from __future__ import annotations

import builtins
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis_core.active_learning import cli as cli_module
from jarvis_core.active_learning.engine import ALConfig, ALStats
from jarvis_core.active_learning.query import (
    BalancedSampling,
    DiversitySampling,
    RandomSampling,
    UncertaintySampling,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(f"{__import__('json').dumps(row, ensure_ascii=False)}\n" for row in rows),
        encoding="utf-8",
    )


def test_load_papers_from_jsonl_uses_multiple_id_fields(tmp_path: Path) -> None:
    path = tmp_path / "papers.jsonl"
    _write_jsonl(
        path,
        [
            {"id": "a1", "title": "one"},
            {"paper_id": "a2", "title": "two"},
            {"pmid": 3, "title": "three"},
            {"title": "missing-id"},
        ],
    )

    papers = cli_module.load_papers_from_jsonl(path)

    assert set(papers.keys()) == {"a1", "a2", "3"}
    assert papers["a1"]["title"] == "one"


def test_extract_features_detects_keywords_and_word_count() -> None:
    paper = {
        "title": "Randomized clinical trial",
        "abstract": "This systematic review reports significant efficacy outcomes.",
    }

    feats = cli_module.extract_features(paper)

    assert len(feats) == 19
    assert feats[0] == 1.0
    assert feats[4] == 1.0
    assert feats[-1] > 0.0


def test_run_screening_session_exits_for_empty_input(tmp_path: Path) -> None:
    inp = tmp_path / "empty.jsonl"
    out = tmp_path / "out.jsonl"
    inp.write_text("", encoding="utf-8")

    with pytest.raises(SystemExit):
        cli_module.run_screening_session(
            input_path=inp,
            output_path=out,
            config=ALConfig(batch_size=2, initial_samples=1),
            interactive=False,
        )


def test_run_screening_session_auto_mode_writes_results(tmp_path: Path) -> None:
    inp = tmp_path / "papers.jsonl"
    out = tmp_path / "labels.jsonl"
    _write_jsonl(
        inp,
        [
            {"id": "p1", "title": "Randomized study", "abstract": "clinical trial"},
            {"id": "p2", "title": "Observational report", "abstract": "retrospective"},
        ],
    )

    stats = cli_module.run_screening_session(
        input_path=inp,
        output_path=out,
        config=ALConfig(batch_size=2, initial_samples=1, budget_ratio=1.0, target_recall=0.99),
        interactive=False,
    )

    lines = [line for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 1
    assert isinstance(stats, ALStats)


def test_run_screening_session_interactive_quit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inp = tmp_path / "papers.jsonl"
    out = tmp_path / "labels.jsonl"
    _write_jsonl(inp, [{"id": "p1", "title": "Study", "abstract": "text"}])
    monkeypatch.setattr("builtins.input", lambda _: "q")

    stats = cli_module.run_screening_session(
        input_path=inp,
        output_path=out,
        config=ALConfig(batch_size=1, initial_samples=1, budget_ratio=1.0),
        interactive=True,
    )

    assert stats.total_instances == 1
    assert out.exists()


def test_cmd_screen_missing_input_exits(tmp_path: Path) -> None:
    args = SimpleNamespace(
        input=str(tmp_path / "missing.jsonl"),
        output=str(tmp_path / "out.jsonl"),
        batch_size=1,
        target_recall=0.9,
        budget_ratio=0.5,
        initial_samples=1,
        auto=True,
        json=False,
    )
    with pytest.raises(SystemExit):
        cli_module.cmd_screen(args)


def test_cmd_screen_prints_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    inp = tmp_path / "papers.jsonl"
    inp.write_text('{"id":"x","title":"t"}\n', encoding="utf-8")

    monkeypatch.setattr(
        cli_module,
        "run_screening_session",
        lambda **_: ALStats(
            total_instances=10,
            labeled_instances=5,
            relevant_found=2,
            iterations=1,
            estimated_recall=0.5,
        ),
    )

    args = SimpleNamespace(
        input=str(inp),
        output=str(tmp_path / "out.jsonl"),
        batch_size=2,
        target_recall=0.9,
        budget_ratio=0.5,
        initial_samples=1,
        auto=True,
        json=True,
    )
    cli_module.cmd_screen(args)
    output = capsys.readouterr().out
    assert '"total_instances": 10' in output


def test_uncertainty_sampling_orders_by_uncertainty() -> None:
    strategy = UncertaintySampling()
    unlabeled = ["a", "b", "c"]
    preds = {"a": 0.51, "b": 0.9, "c": 0.5}
    selected = strategy.select(unlabeled, {}, preds, 2)
    assert selected == ["c", "a"]


def test_diversity_sampling_handles_empty_and_full_request() -> None:
    strategy = DiversitySampling()
    assert strategy.select([], {}, {}, 2) == []

    unlabeled = ["a", "b"]
    result = strategy.select(unlabeled, {"a": [0.0], "b": [1.0]}, {"a": 0.4, "b": 0.6}, 2)
    assert result == unlabeled


def test_diversity_sampling_normal_path() -> None:
    strategy = DiversitySampling(uncertainty_weight=0.5)
    unlabeled = ["a", "b", "c"]
    features = {"a": [0.0, 0.0], "b": [1.0, 0.0], "c": [0.0, 1.0]}
    preds = {"a": 0.5, "b": 0.9, "c": 0.1}
    result = strategy.select(unlabeled, features, preds, 2)
    assert len(result) == 2
    assert result[0] == "a"


def test_diversity_sampling_importerror_falls_back_to_random(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = DiversitySampling()
    unlabeled = ["a", "b", "c"]
    features = {"a": [0.0], "b": [1.0], "c": [2.0]}
    preds = {"a": 0.3, "b": 0.6, "c": 0.5}

    orig_import = builtins.__import__

    def _mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "numpy":
            raise ImportError("forced")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    result = strategy.select(unlabeled, features, preds, 2)

    assert len(result) == 2
    assert set(result).issubset(set(unlabeled))


def test_random_sampling_is_deterministic_for_seed() -> None:
    unlabeled = ["a", "b", "c", "d"]
    s1 = RandomSampling(seed=1).select(unlabeled, {}, {}, 2)
    s2 = RandomSampling(seed=1).select(unlabeled, {}, {}, 2)
    assert s1 == s2


def test_balanced_sampling_interleaves_classes() -> None:
    strategy = BalancedSampling()
    unlabeled = ["a", "b", "c", "d"]
    preds = {"a": 0.9, "b": 0.1, "c": 0.8, "d": 0.2}
    selected = strategy.select(unlabeled, {}, preds, 4)
    assert selected[0] in {"a", "c"}
    assert selected[1] in {"b", "d"}


def test_balanced_sampling_handles_single_class() -> None:
    strategy = BalancedSampling()
    unlabeled = ["a", "b"]
    preds = {"a": 0.8, "b": 0.7}
    assert strategy.select(unlabeled, {}, preds, 5) == ["b", "a"]
