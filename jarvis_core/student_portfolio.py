"""Multi-Student Portfolio Manager.

Per Ψ-6, this manages multiple student research portfolios.
"""
from __future__ import annotations

from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def analyze_student_portfolio(
    portfolios: Dict[str, List["PaperVector"]],
) -> List[dict]:
    """Analyze multiple student research portfolios.

    Args:
        portfolios: Dict mapping student name to their PaperVectors.

    Returns:
        List of portfolio analyses with risk ranking.
    """
    if not portfolios:
        return []

    analyses = []

    for student, vectors in portfolios.items():
        if not vectors:
            analyses.append({
                "student": student,
                "risk_rank": "high",
                "continuation_advice": "研究開始が必要",
                "paper_count": 0,
            })
            continue

        # Analyze portfolio
        avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
        avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)

        # Check focus
        concepts = set()
        for v in vectors:
            concepts.update(v.concept.concepts.keys())
        focus_score = 1 / (1 + len(concepts) / 5)

        # Calculate risk
        risk_score = (1 - avg_novelty) * 0.3 + (1 - avg_impact) * 0.3 + (1 - focus_score) * 0.4

        if risk_score > 0.6:
            risk_rank = "high"
            advice = "テーマ絞り込みと深掘りを推奨"
        elif risk_score > 0.3:
            risk_rank = "medium"
            advice = "現行継続、定期的な方向確認を推奨"
        else:
            risk_rank = "low"
            advice = "順調、論文化を目指す"

        analyses.append({
            "student": student,
            "risk_rank": risk_rank,
            "risk_score": round(risk_score, 2),
            "continuation_advice": advice,
            "paper_count": len(vectors),
            "focus_score": round(focus_score, 2),
            "estimated": True,
        })

    # Sort by risk
    analyses.sort(key=lambda x: x.get("risk_score", 0), reverse=True)

    return analyses
