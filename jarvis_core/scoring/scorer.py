"""Scoring helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoreResult:
    """Result of scoring."""

    score: float = 0.0
    details: dict[str, Any] | None = None


class Scorer:
    """Simple scorer stub."""

    def score(self, inputs: dict[str, float]) -> ScoreResult:
        """Score inputs.

        Args:
            inputs: Input features.

        Returns:
            ScoreResult with summed score.
        """
        total = float(sum(inputs.values())) if inputs else 0.0
        return ScoreResult(score=total, details=dict(inputs))


__all__ = ["Scorer", "ScoreResult"]
