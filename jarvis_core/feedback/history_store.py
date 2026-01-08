"""History storage for feedback entries."""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from .schema import FeedbackEntry, normalize_feedback


class FeedbackHistoryStore:
    """Append-only history store for feedback entries."""

    def __init__(self, path: str = "data/feedback/history.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: FeedbackEntry) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def extend(self, entries: Iterable[FeedbackEntry]) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def list_entries(self, limit: int | None = None) -> list[FeedbackEntry]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
        if limit:
            lines = lines[-limit:]
        entries = [normalize_feedback(json.loads(line)) for line in lines]
        return entries
