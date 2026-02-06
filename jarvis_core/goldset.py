"""Goldset helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Goldset:
    """Goldset container."""

    items: list[str] = field(default_factory=list)


def build_goldset(items: list[str]) -> Goldset:
    """Build a goldset from items.

    Args:
        items: Item list.

    Returns:
        Goldset.
    """
    return Goldset(items=list(items))


__all__ = ["Goldset", "build_goldset"]
