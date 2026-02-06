"""Ranking scorer utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoringResult:
    """Result of scoring."""

    score: float = 0.0
    details: dict[str, Any] | None = None


class Scorer:
    """Simple scoring stub."""

    def score(self, features: dict[str, float]) -> ScoringResult:
        """Score a feature set.

        Args:
            features: Feature dictionary.

        Returns:
            ScoringResult with summed score.
        """
        total = float(sum(features.values())) if features else 0.0
        return ScoringResult(score=total, details=dict(features))


__all__ = ["Scorer", "ScoringResult"]
