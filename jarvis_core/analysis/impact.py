"""Impact analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImpactReport:
    """Lightweight impact report."""

    score: float = 0.0
    summary: str = ""


def assess_impact(text: str) -> ImpactReport:
    """Assess the impact of a text snippet.

    Args:
        text: Input text.

    Returns:
        ImpactReport with a heuristic score.
    """
    if not text:
        return ImpactReport(score=0.0, summary="")
    score = min(1.0, max(0.0, len(text) / 1000.0))
    return ImpactReport(score=score, summary="heuristic")


__all__ = ["ImpactReport", "assess_impact"]
