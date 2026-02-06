"""Replay recording utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReplayRecord:
    """Single replay record."""

    event: str
    payload: dict[str, Any] = field(default_factory=dict)


class ReplayRecorder:
    """Record replay events."""

    def __init__(self) -> None:
        """Initialize recorder."""
        self._records: list[ReplayRecord] = []

    def record(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Record an event.

        Args:
            event: Event name.
            payload: Event payload.
        """
        self._records.append(ReplayRecord(event=event, payload=payload or {}))

    def list_records(self) -> list[ReplayRecord]:
        """Return recorded events."""
        return list(self._records)


__all__ = ["ReplayRecord", "ReplayRecorder"]
