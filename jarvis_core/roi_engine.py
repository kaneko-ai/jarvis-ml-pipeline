"""Research ROI Engine.

Per Ψ-1, this calculates research return on investment.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def calculate_research_roi(
    vectors: list[PaperVector],
    time_invested_months: float = 12,
) -> dict:
    """Calculate research ROI score.

    Args:
        vectors: PaperVectors representing research output.
        time_invested_months: Time invested in months.

    Returns:
        ROI analysis with score and opportunity cost.
    """
    if not vectors or time_invested_months <= 0:
        return {
            "roi_score": 0.0,
            "opportunity_cost": "high",
            "reason": "データ不足",
            "estimated": True,
        }

    # Calculate output value
    total_impact = sum(v.impact.future_potential for v in vectors)
    total_novelty = sum(v.temporal.novelty for v in vectors)
    output_value = (total_impact + total_novelty) / 2

    # Normalize by time
    monthly_output = output_value / time_invested_months
    roi_score = min(1.0, monthly_output * 2)

    # Opportunity cost assessment
    if roi_score > 0.6:
        opportunity_cost = "low"
        reason = "高い研究生産性"
    elif roi_score > 0.3:
        opportunity_cost = "medium"
        reason = "標準的な進捗"
    else:
        opportunity_cost = "high"
        reason = "効率改善の余地あり"

    return {
        "roi_score": round(roi_score, 3),
        "opportunity_cost": opportunity_cost,
        "reason": reason,
        "monthly_output": round(monthly_output, 3),
        "total_papers": len(vectors),
        "estimated": True,
    }
