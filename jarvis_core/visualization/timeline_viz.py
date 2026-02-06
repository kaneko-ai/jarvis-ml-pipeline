"""Timeline visualization helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TimelinePoint:
    """Single timeline point."""

    label: str
    value: float


class TimelineVisualizer:
    """Minimal timeline visualizer."""

    def render(self, points: list[TimelinePoint]) -> dict:
        """Render timeline points.

        Args:
            points: Timeline points.

        Returns:
            Dict representation for testing.
        """
        return {"count": len(points), "points": points}


__all__ = ["TimelinePoint", "TimelineVisualizer"]
