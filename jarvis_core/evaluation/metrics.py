"""Compatibility metrics module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Metrics:
    """Simple binary metrics helper for compatibility tests."""

    def accuracy(self, y_true: list[int], y_pred: list[int]) -> float:
        if not y_true:
            return 0.0
        matched = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        return matched / max(1, len(y_true))
