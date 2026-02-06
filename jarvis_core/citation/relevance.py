"""Citation relevance helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RelevanceScore:
    """Relevance score for a citation."""

    score: float = 0.0


def score_relevance(text: str) -> RelevanceScore:
    """Score relevance of a citation text.

    Args:
        text: Citation text.

    Returns:
        RelevanceScore.
    """
    _ = text
    return RelevanceScore(score=0.0)


__all__ = ["RelevanceScore", "score_relevance"]
