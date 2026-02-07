"""Compatibility metrics helpers."""

from __future__ import annotations


def accuracy(predictions: list[int] | None = None, targets: list[int] | None = None) -> float:
    """Compute simple accuracy."""
    predictions = predictions or []
    targets = targets or []
    if not predictions or not targets or len(predictions) != len(targets):
        return 0.0
    return sum(1 for p, t in zip(predictions, targets) if p == t) / len(targets)


class Metrics:
    """Small wrapper class for compatibility tests."""

    def compute(
        self, predictions: list[int] | None = None, targets: list[int] | None = None
    ) -> dict[str, float]:
        """Compute metric dictionary."""
        return {"accuracy": accuracy(predictions, targets)}
