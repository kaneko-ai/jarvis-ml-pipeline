"""Kill-Switch Recommendation Engine.

Per Ψ-7, this recommends when to stop research themes.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def recommend_kill_switch(
    theme: str,
    vectors: List["PaperVector"],
    months_invested: int = 12,
) -> dict:
    """Recommend whether to stop a research theme.

    Args:
        theme: Research theme name.
        vectors: PaperVectors for this theme.
        months_invested: Time already invested.

    Returns:
        Kill-switch recommendation.
    """
    if not vectors:
        return {
            "stop_score": 0.8,
            "recommendation": "stop",
            "evidence": ["成果物なし"],
            "estimated": True,
        }

    evidence = []

    # Check output rate
    papers_per_year = len(vectors) / (months_invested / 12)
    if papers_per_year < 1:
        evidence.append("年間論文数が1未満")

    # Check novelty trend
    sorted_vectors = sorted(vectors, key=lambda v: v.metadata.year or 0)
    if len(sorted_vectors) >= 2:
        early_novelty = sorted_vectors[0].temporal.novelty
        late_novelty = sorted_vectors[-1].temporal.novelty
        if late_novelty < early_novelty - 0.2:
            evidence.append("新規性が低下傾向")

    # Check impact
    avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)
    if avg_impact < 0.3:
        evidence.append("将来インパクトが低い")

    # Check field saturation
    from .sigma_modules import assess_field_saturation
    sat = assess_field_saturation(vectors, theme)
    if sat.get("saturation", 0) > 0.7:
        evidence.append("分野が飽和状態")

    # Calculate stop score
    stop_score = min(1.0, len(evidence) * 0.25)

    if stop_score >= 0.6:
        recommendation = "stop"
    elif stop_score >= 0.3:
        recommendation = "pivot"
    else:
        recommendation = "continue"

    return {
        "theme": theme,
        "stop_score": round(stop_score, 2),
        "recommendation": recommendation,
        "evidence": evidence if evidence else ["中止根拠なし"],
        "months_invested": months_invested,
        "estimated": True,
    }
