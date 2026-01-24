"""Lab Culture Risk Detector.

Per Ψ-8, this detects research culture risks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def detect_lab_culture_risk(
    vectors: list[PaperVector],
) -> dict:
    """Detect lab culture risks from research patterns.

    Args:
        vectors: PaperVectors representing lab output.

    Returns:
        Culture risk assessment.
    """
    if not vectors:
        return {"culture_risk_index": 0.5, "risks": [], "estimated": True}

    risks = []
    risk_score = 0.0

    # Check reproducibility light (minimal method variation)
    methods = set()
    for v in vectors:
        methods.update(v.method.methods.keys())

    if len(methods) < 3:
        risks.append("手法の多様性不足（検証軽視リスク）")
        risk_score += 0.2

    # Check trend-chasing (all recent high-novelty but low depth)
    novelty_values = [v.temporal.novelty for v in vectors]
    avg_novelty = sum(novelty_values) / len(novelty_values)
    novelty_variance = sum((n - avg_novelty) ** 2 for n in novelty_values) / len(novelty_values)

    if avg_novelty > 0.7 and novelty_variance < 0.05:
        risks.append("トレンド追従傾向（流行重視の懸念）")
        risk_score += 0.2

    # Check concept spreading (too many concepts, low depth each)
    concepts = {}
    for v in vectors:
        for c in v.concept.concepts:
            concepts[c] = concepts.get(c, 0) + 1

    if len(concepts) > 10 and max(concepts.values()) < 3:
        risks.append("研究テーマの拡散（深掘り不足）")
        risk_score += 0.15

    # Check impact consistency
    impacts = [v.impact.future_potential for v in vectors]
    if max(impacts) - min(impacts) > 0.5:
        risks.append("成果品質のばらつき")
        risk_score += 0.1

    risk_score = min(1.0, risk_score)

    return {
        "culture_risk_index": round(risk_score, 2),
        "risks": risks if risks else ["特定のリスク検出なし"],
        "method_diversity": len(methods),
        "concept_spread": len(concepts),
        "estimated": True,
    }
