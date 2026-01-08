"""Funding Cliff Predictor.

Per Ψ-10, this predicts funding gaps.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def predict_funding_cliff(
    vectors: list[PaperVector],
    current_funding_months: int = 24,
    publication_rate: float = 2.0,
) -> dict:
    """Predict funding cliff and suggest mitigation.

    Args:
        vectors: PaperVectors representing current output.
        current_funding_months: Remaining funding in months.
        publication_rate: Expected publications per year.

    Returns:
        Funding cliff prediction.
    """
    if not vectors:
        return {
            "months_to_cliff": current_funding_months,
            "mitigation": ["研究実績の蓄積が急務"],
            "estimated": True,
        }

    # Analyze current momentum
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)

    # Momentum score affects funding sustainability
    momentum = (avg_novelty + avg_impact) / 2

    # Adjust cliff based on momentum
    if momentum > 0.6:
        adjustment = 6  # Good momentum extends runway
    elif momentum > 0.3:
        adjustment = 0
    else:
        adjustment = -6  # Poor momentum shortens runway

    months_to_cliff = max(0, current_funding_months + adjustment)

    # Mitigation strategies
    mitigation = []

    if months_to_cliff < 12:
        mitigation.append("緊急グラント申請を開始")
        mitigation.append("共同研究先の資金活用を検討")

    if momentum < 0.5:
        mitigation.append("研究テーマの見直しで競争力強化")

    if publication_rate < 1.5:
        mitigation.append("論文発表ペースの加速")

    if not mitigation:
        mitigation.append("現状維持可能、次期グラント準備を開始")

    return {
        "months_to_cliff": months_to_cliff,
        "momentum_score": round(momentum, 2),
        "mitigation": mitigation,
        "urgency": "high" if months_to_cliff < 12 else ("medium" if months_to_cliff < 24 else "low"),
        "estimated": True,
    }
