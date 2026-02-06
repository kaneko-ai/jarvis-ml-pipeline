"""Observation collector helpers."""

from __future__ import annotations


class ObsCollector:
    """Minimal observation collector."""

    def collect(self) -> list[dict]:
        """Return an empty list of observations."""
        return []
