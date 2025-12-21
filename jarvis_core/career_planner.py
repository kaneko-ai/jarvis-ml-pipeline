"""Research Career Strategy Planner.

Per Issue Ω-6, this plans research career trajectory.
"""
from __future__ import annotations

from typing import List, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def plan_career_strategy(
    vectors: List["PaperVector"],
    current_stage: Literal["phd", "postdoc", "pi"] = "phd",
) -> dict:
    """Plan research career strategy.

    Args:
        vectors: PaperVectors representing research portfolio.
        current_stage: Current career stage.

    Returns:
        Career strategy plan.
    """
    if not vectors:
        return {
            "stage": current_stage,
            "recommendations": ["研究実績の蓄積が必要"],
            "estimated": True,
        }

    # Analyze research portfolio
    concepts = {}
    methods = {}
    years = []

    for v in vectors:
        for c, score in v.concept.concepts.items():
            concepts[c] = concepts.get(c, 0) + score
        for m, score in v.method.methods.items():
            methods[m] = methods.get(m, 0) + score
        if v.metadata.year:
            years.append(v.metadata.year)

    # Calculate metrics
    focus_score = max(concepts.values()) if concepts else 0
    breadth = len(concepts)
    technical_depth = len(methods)

    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)

    recommendations = []
    risks = []

    if current_stage == "phd":
        if breadth > 5:
            recommendations.append("研究テーマの絞り込みを検討")
        else:
            recommendations.append("コアコンピタンスの確立は良好")

        if technical_depth < 3:
            recommendations.append("技術スキルの幅を広げることを推奨")

        if avg_novelty < 0.5:
            risks.append("独自性の確立が課題")

        next_milestone = "博士論文完成と1本以上の筆頭論文"

    elif current_stage == "postdoc":
        if breadth < 3:
            recommendations.append("研究の幅を広げる機会を模索")

        if avg_impact < 0.5:
            recommendations.append("インパクトの高い研究テーマへのシフトを検討")

        recommendations.append("独立に向けた独自研究ラインの確立")
        next_milestone = "独立研究テーマの確立とグラント獲得"

    else:  # pi
        recommendations.append("研究室の方向性の明確化")
        if focus_score < 0.5:
            recommendations.append("研究室の強みとなる領域の特定が必要")

        recommendations.append("次世代研究者の育成計画")
        next_milestone = "持続可能な研究プログラムの確立"

    return {
        "stage": current_stage,
        "portfolio_analysis": {
            "focus_score": round(focus_score, 2),
            "breadth": breadth,
            "technical_depth": technical_depth,
            "novelty": round(avg_novelty, 2),
            "impact": round(avg_impact, 2),
        },
        "top_concepts": sorted(concepts.items(), key=lambda x: x[1], reverse=True)[:5],
        "recommendations": recommendations,
        "risks": risks,
        "next_milestone": next_milestone,
        "estimated": True,
    }
