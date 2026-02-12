from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.repair.learner import RepairRecord, SelfRepairLearner, get_learner


def test_repair_record_roundtrip() -> None:
    record = RepairRecord(
        fail_reason="timeout",
        repair_action="retry",
        success=True,
        attempts=2,
        timestamp="t",
        context={"k": 1},
    )
    data = record.to_dict()
    loaded = RepairRecord.from_dict(data)
    assert loaded.fail_reason == "timeout"
    assert loaded.context["k"] == 1


def test_self_repair_learner_record_analyze_recommend_and_stats(tmp_path: Path) -> None:
    history = tmp_path / "repair.jsonl"
    learner = SelfRepairLearner(history)

    learner.record("timeout", "retry", True, attempts=1)
    learner.record("timeout", "retry", False, attempts=3)
    learner.record("timeout", "increase_timeout", True, attempts=2)
    learner.record("schema", "fix_parser", False, attempts=1)

    strategies = learner.analyze_strategies("timeout")
    assert strategies
    assert strategies[0].success_rate >= strategies[-1].success_rate

    best = learner.get_best_strategy("timeout")
    assert best is not None
    assert best.recommended is True

    stats = learner.get_statistics()
    assert stats["total_records"] == 4
    assert "timeout" in stats["by_reason"]

    recommendations = learner.recommend_actions(["timeout", "unknown"])
    assert recommendations[0]["recommended_action"] in {"retry", "increase_timeout"}
    assert recommendations[1]["recommended_action"] is None


def test_self_repair_learner_load_history_error_path(
    tmp_path: Path, monkeypatch
) -> None:  # noqa: ANN001
    bad_history = tmp_path / "bad.jsonl"
    bad_history.parent.mkdir(parents=True, exist_ok=True)
    bad_history.write_text("{bad json\n", encoding="utf-8")

    learner = SelfRepairLearner(bad_history)
    assert learner.get_statistics()["total_records"] == 0

    default_history = tmp_path / "default.jsonl"
    monkeypatch.setattr("jarvis_core.repair.learner.Path", lambda *args, **kwargs: default_history)
    got = get_learner()
    assert isinstance(got, SelfRepairLearner)
    assert got.history_path == default_history

    # ensure line format remains jsonl
    got.record("f", "a", True)
    line = default_history.read_text(encoding="utf-8").splitlines()[0]
    assert json.loads(line)["fail_reason"] == "f"
