"""Provenance tracking helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProvenanceEvent:
    """Single provenance event."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)


class ProvenanceTracker:
    """Track provenance events in memory."""

    def __init__(self) -> None:
        """Initialize tracker."""
        self._events: list[ProvenanceEvent] = []

    def record(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Record a provenance event.

        Args:
            name: Event name.
            payload: Event payload.
        """
        self._events.append(ProvenanceEvent(name=name, payload=payload or {}))

    def list_events(self) -> list[ProvenanceEvent]:
        """Return recorded events."""
        return list(self._events)


__all__ = ["ProvenanceEvent", "ProvenanceTracker"]
