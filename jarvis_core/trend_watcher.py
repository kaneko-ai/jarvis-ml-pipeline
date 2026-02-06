"""Trend watcher helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrendSignal:
    """Trend signal."""

    direction: str = "flat"


def watch_trend(values: list[float]) -> TrendSignal:
    """Watch trend from values.

    Args:
        values: Numeric series.

    Returns:
        TrendSignal.
    """
    if len(values) < 2:
        return TrendSignal(direction="flat")
    direction = "up" if values[-1] > values[0] else "down" if values[-1] < values[0] else "flat"
    return TrendSignal(direction=direction)


__all__ = ["TrendSignal", "watch_trend"]
