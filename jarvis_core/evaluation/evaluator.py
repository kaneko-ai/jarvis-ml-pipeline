"""Compatibility evaluator module for evaluation package."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Simple evaluation result container."""

    score: float = 0.0
    passed: bool = False


class Evaluator:
    """Minimal evaluator used by broad compatibility tests."""

    def evaluate(
        self, predictions: list[float] | None = None, targets: list[float] | None = None
    ) -> EvaluationResult:
        """Evaluate predictions against targets."""
        predictions = predictions or []
        targets = targets or []
        if not predictions or not targets or len(predictions) != len(targets):
            return EvaluationResult(score=0.0, passed=False)
        matches = sum(1 for p, t in zip(predictions, targets) if p == t)
        score = matches / len(targets)
        return EvaluationResult(score=score, passed=score >= 0.5)
