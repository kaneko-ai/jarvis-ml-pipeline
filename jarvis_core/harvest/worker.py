"""Queue worker for harvest work mode."""

from __future__ import annotations

import json
from pathlib import Path

from .budget import HarvestBudget
from .queue import HarvestQueue


def process_queue(*, run_dir: Path, budget: HarvestBudget, oa_only: bool = True) -> dict:
    harvest_dir = run_dir / "harvest"
    queue = HarvestQueue(harvest_dir / "queue.jsonl")
    rows = queue.load()
    items_dir = harvest_dir / "items"
    items_dir.mkdir(parents=True, exist_ok=True)

    budget.start()
    processed = 0
    skipped = 0
    failed = 0

    for row in rows:
        if row.get("status") != "queued":
            continue
        if budget.is_exceeded():
            break
        budget.consume_request()
        paper_key = (
            str(row.get("paper_key", "unknown"))
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )
        item_dir = items_dir / paper_key
        item_dir.mkdir(parents=True, exist_ok=True)
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else row
        pmc_id = str(row.get("pmc_id") or "")
        if oa_only and not pmc_id:
            row["status"] = "skipped"
            row["reason"] = "OA_NOT_AVAILABLE"
            skipped += 1
            continue
        try:
            (item_dir / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            row["status"] = "done"
            processed += 1
            budget.consume_item()
        except Exception as exc:
            row["status"] = "failed"
            row["reason"] = str(exc)
            failed += 1

    queue.save(rows)

    stats = {
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "queue_total": len(rows),
        "queue_pending": sum(1 for row in rows if row.get("status") == "queued"),
        "budget": {
            "max_items": budget.max_items,
            "max_minutes": budget.max_minutes,
            "max_requests": budget.max_requests,
            "items_done": budget.items_done,
            "requests_done": budget.requests_done,
            "exceeded": budget.is_exceeded(),
        },
    }
    return stats
