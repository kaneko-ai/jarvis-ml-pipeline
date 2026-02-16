from __future__ import annotations

from pathlib import Path

from jarvis_core.harvest.queue import HarvestQueue
from jarvis_core.harvest.runner import run_work


def test_harvest_budget_exceeded_and_resume(tmp_path: Path):
    out_dir = tmp_path / "runs"
    run_id = "harvest_resume_run"
    run_dir = out_dir / run_id
    queue = HarvestQueue(run_dir / "harvest" / "queue.jsonl")
    queue.enqueue_many(
        [
            {"paper_key": "pmid:1", "metadata": {"pmid": "1", "title": "A"}},
            {"paper_key": "pmid:2", "metadata": {"pmid": "2", "title": "B"}},
        ]
    )

    first = run_work(
        budget_raw="max_items=1,max_minutes=30,max_requests=100",
        out=str(out_dir),
        out_run=run_id,
        oa_only=False,
    )
    assert first["status"] == "needs_retry"

    second = run_work(
        budget_raw="max_items=10,max_minutes=30,max_requests=100",
        out=str(out_dir),
        out_run=run_id,
        oa_only=False,
    )
    assert second["status"] == "success"
    rows = queue.load()
    assert sum(1 for row in rows if row.get("status") == "queued") == 0
