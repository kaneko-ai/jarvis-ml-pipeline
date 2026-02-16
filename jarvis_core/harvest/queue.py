"""Run-scoped queue persistence for harvest."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class HarvestQueue:
    def __init__(self, queue_path: Path):
        self.queue_path = queue_path
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict]:
        if not self.queue_path.exists():
            return []
        rows: list[dict] = []
        for line in self.queue_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        return rows

    def save(self, rows: list[dict]) -> None:
        data = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + (
            "\n" if rows else ""
        )
        self.queue_path.write_text(data, encoding="utf-8")

    def enqueue_many(self, items: list[dict]) -> int:
        rows = self.load()
        existing = {str(r.get("paper_key", "")) for r in rows}
        added = 0
        for item in items:
            key = str(item.get("paper_key", "")).strip()
            if not key or key in existing:
                continue
            row = {
                **item,
                "status": "queued",
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
            rows.append(row)
            existing.add(key)
            added += 1
        self.save(rows)
        return added
