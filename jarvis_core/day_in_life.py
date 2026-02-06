"""Day-in-life narrative helpers."""

from __future__ import annotations


def build_day_in_life(name: str) -> str:
    """Build a simple day-in-life narrative.

    Args:
        name: Person name.

    Returns:
        Narrative string.
    """
    return f"{name} starts the day with a focused research session."


__all__ = ["build_day_in_life"]
