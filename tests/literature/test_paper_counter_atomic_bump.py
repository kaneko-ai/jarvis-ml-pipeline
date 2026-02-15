from __future__ import annotations

from pathlib import Path

from jarvis_core.literature.paper_counter import PaperCounterStore


def test_paper_counter_atomic_bump(tmp_path: Path) -> None:
    store = PaperCounterStore(tmp_path / "papers.json")
    store.init_if_missing()
    store.bump(run_id="r1", field="discovered", delta=1)
    store.bump(run_id="r1", field="downloaded", delta=2)
    snap = store.snapshot()
    assert snap["totals"]["discovered"] == 1
    assert snap["totals"]["downloaded"] == 2
    assert snap["by_run"]["r1"]["discovered"] == 1
    assert snap["by_run"]["r1"]["downloaded"] == 2
