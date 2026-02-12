from __future__ import annotations

from pathlib import Path

from jarvis_core.storage.run_store_index import RunRecord, RunStoreIndex


def _rec(run_id: str, status: str, created_at: str, category: str = "general") -> RunRecord:
    return RunRecord(
        run_id=run_id,
        status=status,
        category=category,
        created_at=created_at,
        query=f"q-{run_id}",
        docs_count=2,
        claims_count=3,
        duration_seconds=1.2,
    )


def test_run_store_index_add_get_list_and_counts(tmp_path: Path) -> None:
    db = tmp_path / "runs.db"
    store = RunStoreIndex(str(db))

    store.add(_rec("r1", "ok", "2026-01-01T10:00:00"))
    store.add(_rec("r2", "failed", "2026-01-03T10:00:00", category="bio"))
    store.add(_rec("r3", "ok", "2026-01-02T10:00:00", category="bio"))

    got = store.get("r1")
    assert got is not None
    assert got.status == "ok"

    assert store.get("missing") is None

    recent = store.list_recent(limit=2)
    assert [r.run_id for r in recent] == ["r2", "r3"]

    by_status = store.list_by_status("ok")
    assert {r.run_id for r in by_status} == {"r1", "r3"}

    counts = store.count_by_status()
    assert counts["ok"] == 2
    assert counts["failed"] == 1


def test_run_store_index_search_filters(tmp_path: Path) -> None:
    db = tmp_path / "runs.db"
    store = RunStoreIndex(str(db))

    store.add(_rec("a", "ok", "2026-01-01T00:00:00", category="x"))
    store.add(_rec("b", "ok", "2026-01-02T00:00:00", category="y"))
    store.add(_rec("c", "failed", "2026-01-03T00:00:00", category="x"))

    all_rows = store.search(limit=10)
    assert [r.run_id for r in all_rows] == ["c", "b", "a"]

    filtered = store.search(status="ok", category="y", since="2026-01-01", limit=10)
    assert [r.run_id for r in filtered] == ["b"]

    since_rows = store.search(since="2026-01-02", limit=10)
    assert [r.run_id for r in since_rows] == ["c", "b"]
