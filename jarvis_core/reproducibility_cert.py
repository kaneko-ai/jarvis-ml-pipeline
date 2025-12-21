"""Reproducibility Certification Mode.

Per Ψ-3, this certifies reproducibility of hypotheses.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def certify_reproducibility(
    hypothesis: str,
    vectors: List["PaperVector"],
) -> dict:
    """Certify reproducibility score for a hypothesis.

    Args:
        hypothesis: The hypothesis to certify.
        vectors: Supporting paper vectors.

    Returns:
        Reproducibility certification.
    """
    if not hypothesis or not vectors:
        return {
            "reproducibility_score": 0.0,
            "weak_points": ["データ不足"],
            "certified": False,
            "estimated": True,
        }

    # Analyze supporting evidence
    weak_points = []

    # Check method consistency
    all_methods = {}
    for v in vectors:
        for m in v.method.methods:
            all_methods[m] = all_methods.get(m, 0) + 1

    if len(all_methods) > 5:
        weak_points.append("手法が分散しすぎ")

    # Check paper count
    if len(vectors) < 3:
        weak_points.append("裏付け論文が少ない")

    # Check year spread
    years = [v.metadata.year for v in vectors if v.metadata.year]
    if years:
        year_spread = max(years) - min(years)
        if year_spread < 2:
            weak_points.append("時間的再現性の検証不足")

    # Check impact variance
    impacts = [v.impact.future_potential for v in vectors]
    if impacts:
        variance = sum((x - sum(impacts)/len(impacts))**2 for x in impacts) / len(impacts)
        if variance > 0.1:
            weak_points.append("評価のばらつきが大きい")

    # Calculate score
    base_score = 0.7
    penalty = 0.15 * len(weak_points)
    reproducibility_score = max(0, base_score - penalty)

    return {
        "reproducibility_score": round(reproducibility_score, 2),
        "weak_points": weak_points,
        "certified": reproducibility_score >= 0.6,
        "supporting_papers": len(vectors),
        "method_count": len(all_methods),
        "estimated": True,
    }
