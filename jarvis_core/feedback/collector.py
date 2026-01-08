"""Collector for past feedback (semi-automatic)."""

from __future__ import annotations

import re
from datetime import datetime

from .history_store import FeedbackHistoryStore
from .schema import FeedbackEntry, normalize_feedback

_KEY_VALUE = re.compile(r"(\w+)\s*[:=]\s*([^|,]+)")


class FeedbackCollector:
    """Parse and normalize feedback from text inputs."""

    def __init__(self, store: FeedbackHistoryStore | None = None):
        self.store = store or FeedbackHistoryStore()

    def parse_text(
        self,
        text: str,
        source: str = "email",
        reviewer: str = "unknown",
        document_type: str = "draft",
        date: str | None = None,
    ) -> list[FeedbackEntry]:
        """Parse feedback text into normalized entries.

        Each line should contain key/value tokens, e.g.
        "category: evidence | severity: major | location: paragraph:12 | message: 根拠不足"
        """
        entries: list[FeedbackEntry] = []
        date = date or datetime.now().strftime("%Y-%m-%d")

        for idx, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = dict((k.lower(), v.strip()) for k, v in _KEY_VALUE.findall(line))
            location = self._parse_location(tokens.get("location", "paragraph:0"))
            entry_data: dict[str, object] = {
                "feedback_id": f"FB-{date.replace('-', '')}-{idx:03d}",
                "source": tokens.get("source", source).lower(),
                "reviewer": tokens.get("reviewer", reviewer).lower(),
                "date": date,
                "document_type": tokens.get("document_type", document_type).lower(),
                "location": location,
                "category": tokens.get("category", "expression").lower(),
                "severity": tokens.get("severity", "minor").lower(),
                "message": tokens.get("message", line),
                "resolved": tokens.get("resolved", "false").lower() == "true",
                "resolution_type": tokens.get("resolution_type", "unknown").lower(),
                "notes": tokens.get("notes", "needs_review"),
                "raw": {"line": line},
            }
            entry = normalize_feedback(entry_data)
            entries.append(entry)

        return entries

    def save_entries(self, entries: list[FeedbackEntry]) -> None:
        """Append entries to history store."""
        self.store.extend(entries)

    def _parse_location(self, raw: str) -> dict[str, int]:
        parts = raw.split(":")
        if len(parts) >= 2:
            return {"type": parts[0].strip(), "index": int(parts[1])}
        return {"type": "paragraph", "index": 0}
