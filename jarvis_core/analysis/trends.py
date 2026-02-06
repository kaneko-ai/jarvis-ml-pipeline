"""Trend analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrendSummary:
    """Summary of a simple trend."""

    slope: float = 0.0
    direction: str = "flat"


def summarize_trends(values: list[float]) -> TrendSummary:
    """Summarize trend direction from a series of values.

    Args:
        values: Sequence of numeric values.

    Returns:
        TrendSummary with slope and direction.
    """
    if len(values) < 2:
        return TrendSummary()
    slope = values[-1] - values[0]
    if slope > 0:
        direction = "up"
    elif slope < 0:
        direction = "down"
    else:
        direction = "flat"
    return TrendSummary(slope=slope, direction=direction)


__all__ = ["TrendSummary", "summarize_trends"]
