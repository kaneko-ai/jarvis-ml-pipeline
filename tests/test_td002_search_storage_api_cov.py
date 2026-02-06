from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from jarvis_core.api import run_api as run_api_module
from jarvis_core.search import engine as search_engine_module
from jarvis_core.search import hybrid as hybrid_module
from jarvis_core.storage import retention as retention_module


def test_search_engine_bm25_and_load_search(tmp_path: Path) -> None:
    bm25 = search_engine_module.BM25Index()
    bm25.add_documents([{"text": "alpha beta"}, {"text": "beta gamma"}])
    scores = bm25.search("beta", top_k=2)
    assert len(scores) == 2
    assert bm25._tokenize("Alpha-2 beta") == ["alpha", "beta"]

    chunks_path = tmp_path / "chunks.jsonl"
    rows = [
        {
            "chunk_id": "c1",
            "paper_id": "p1",
            "paper_title": "Paper 1",
            "text": "This method improves alpha performance.",
            "section": "results",
            "paragraph_index": 1,
            "char_start": 0,
            "char_end": 20,
        },
        {
            "chunk_id": "c2",
            "paper_id": "p2",
            "paper_title": "Paper 2",
            "text": "Gamma baseline with no alpha term.",
            "section": "abstract",
            "paragraph_index": 1,
            "char_start": 0,
            "char_end": 20,
        },
    ]
    with open(chunks_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    engine = search_engine_module.SearchEngine()
    assert engine.load_chunks(chunks_path) == 2
    empty_engine = search_engine_module.SearchEngine()
    assert empty_engine.load_chunks(tmp_path / "missing.jsonl") == 0

    res = engine.search("alpha", top_k=2)
    assert res.total >= 1
    assert res.query == "alpha"
    assert res.results[0].to_dict()["chunk_id"]

    filtered = engine.search("alpha", top_k=5, filters={"paper_id": "p1"})
    assert all(r.paper_id == "p1" for r in filtered.results)
    assert engine._extract_highlights("A. B alpha. C alpha?", "alpha")


def test_search_engine_global_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_results = search_engine_module.SearchResults(query="q", total=0)
    fake_engine = SimpleNamespace(search=lambda query, top_k=10: fake_results)
    monkeypatch.setattr(search_engine_module, "_engine", fake_engine)
    assert search_engine_module.get_search_engine() is fake_engine
    assert search_engine_module.search("q") is fake_results


def test_hybrid_search_weighted_and_rrf(monkeypatch: pytest.MonkeyPatch) -> None:
    bm25_results = search_engine_module.SearchResults(
        results=[
            search_engine_module.SearchResult(
                chunk_id="c1",
                paper_id="p1",
                paper_title="P1",
                text="alpha text",
                score=2.0,
                locator={},
            ),
            search_engine_module.SearchResult(
                chunk_id="c2",
                paper_id="p2",
                paper_title="P2",
                text="beta text",
                score=1.0,
                locator={},
            ),
        ],
        total=2,
        query="alpha",
        took_ms=1.0,
    )
    fake_search_engine = SimpleNamespace(search=lambda *_args, **_kwargs: bm25_results)
    monkeypatch.setattr("jarvis_core.search.get_search_engine", lambda: fake_search_engine)

    engine = hybrid_module.HybridSearchEngine(bm25_weight=0.7, vector_weight=0.3, rrf_k=10)
    monkeypatch.setattr(
        engine,
        "_vector_search",
        lambda _query, _k: [
            {"chunk_id": "c1", "paper_id": "p1", "text": "alpha text", "score": 0.9},
            {"chunk_id": "c3", "paper_id": "p3", "text": "gamma text", "score": 0.8},
        ],
    )

    weighted = engine.search("alpha", top_k=3, method="weighted")
    assert weighted and weighted[0].rank == 1
    assert weighted[0].to_dict()["chunk_id"]

    rrf = engine.search("alpha", top_k=3, method="rrf")
    assert rrf and rrf[0].rank == 1

    monkeypatch.setattr(
        hybrid_module.HybridSearchEngine,
        "search",
        lambda self, query, top_k=20: [  # noqa: ARG005
            hybrid_module.HybridSearchResult(chunk_id="x", paper_id="p", text="t", rank=1)
        ],
    )
    helper = hybrid_module.hybrid_search("query", top_k=1, bm25_weight=0.4)
    assert helper[0].chunk_id == "x"


def _write_events(run_dir: Path, ts: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "events.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts}) + "\n")


def test_storage_retention_policy_paths(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    old_run = runs_dir / "run-old"
    new_run = runs_dir / "run-new"
    important_run = runs_dir / "run-important"

    old_ts = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    new_ts = datetime.now(timezone.utc).isoformat()
    _write_events(old_run, old_ts)
    _write_events(new_run, new_ts)
    _write_events(important_run, old_ts)
    (important_run / ".important").write_text("", encoding="utf-8")
    (old_run / "payload.txt").write_text("x" * 200, encoding="utf-8")

    assert retention_module.get_run_age(old_run) is not None
    assert retention_module.get_run_age(tmp_path / "missing") is None
    assert retention_module.get_run_size(old_run) > 0
    assert retention_module.is_important_run(important_run)

    dry = retention_module.apply_retention_policy(
        str(runs_dir),
        retention_module.RetentionPolicy(max_age_days=30, max_size_gb=0.0000001, keep_latest_n=1),
        dry_run=True,
    )
    assert dry.deleted_runs

    real = retention_module.apply_retention_policy(
        str(runs_dir),
        retention_module.RetentionPolicy(max_age_days=30, max_size_gb=0.0000001, keep_latest_n=1),
        dry_run=False,
    )
    assert isinstance(real, retention_module.CleanupResult)
    assert retention_module.apply_retention_policy(str(tmp_path / "none")).kept_runs == 0


def test_run_api_and_ui_provider_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    api = run_api_module.RunAPI(str(runs_dir))

    class _FakeRunCtx:
        def __init__(self) -> None:
            self.run_id = "run-ctx"
            self.saved: dict[str, Any] | None = None

        def save_config(self, config: dict[str, Any]) -> None:
            self.saved = config

    class _FakeStore:
        def __init__(self, _path: str) -> None:
            self.ctx = _FakeRunCtx()

        def create_run(self) -> _FakeRunCtx:
            return self.ctx

    monkeypatch.setattr("jarvis_core.storage.run_store_v2.RunStore", _FakeStore)
    started = api.start_run({"goal": "x"})
    assert started["run_id"] == "run-ctx"

    run_path = runs_dir / "run-1"
    run_path.mkdir()
    (run_path / "result.json").write_text(
        json.dumps(
            {"status": "done", "timestamp": "2026-02-06", "answer": "A", "citations": ["c1"]}
        ),
        encoding="utf-8",
    )
    (run_path / "eval_summary.json").write_text(
        json.dumps({"gate_passed": True, "fail_reasons": [], "metrics": {"p": 1}}),
        encoding="utf-8",
    )
    (run_path / "papers.jsonl").write_text(json.dumps({"doc_id": "p1"}) + "\n", encoding="utf-8")
    (run_path / "warnings.jsonl").write_text(json.dumps({"warning": "w"}) + "\n", encoding="utf-8")
    for required in [
        "input.json",
        "run_config.json",
        "claims.jsonl",
        "evidence.jsonl",
        "scores.json",
        "report.md",
    ]:
        (run_path / required).write_text("{}", encoding="utf-8")

    assert api.get_status("run-1")["status"] == "done"
    assert api.get_status("missing") is None
    assert api.get_eval_summary("run-1")["gate_passed"] is True
    assert api.get_eval_summary("missing") is None
    listed = api.list_runs(limit=5)
    assert listed and listed[0]["run_id"] == "run-1"

    ui = run_api_module.UIDataProvider(str(runs_dir))
    display = ui.get_run_display("run-1")
    assert display["run_id"] == "run-1"
    assert display["bundle_complete"] is True
    assert ui.get_run_display("missing")["error"] == "Run not found"
