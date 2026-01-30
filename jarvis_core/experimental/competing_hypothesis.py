"""Competing Hypothesis Generator.

Per RP40, this generates alternative hypotheses for phenomena.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def generate_competing_hypotheses(
    phenomenon: str,
    vectors: list[PaperVector],
) -> list[dict]:
    """Generate competing hypotheses for a phenomenon.

    Args:
        phenomenon: The phenomenon to explain.
        vectors: PaperVectors for context.

    Returns:
        List of competing hypothesis dicts.
    """
    if not phenomenon or not vectors:
        return []

    # Find relevant papers
    phenomenon_lower = phenomenon.lower()
    relevant = []
    for v in vectors:
        for c in v.concept.concepts:
            if phenomenon_lower in c.lower() or c.lower() in phenomenon_lower:
                relevant.append(v)
                break

    if not relevant:
        # Default hypotheses when no context
        return [
            {
                "id": "hyp_1",
                "hypothesis": f"{phenomenon}は直接的な機序によって引き起こされる",
                "conflicts_with": ["hyp_2"],
                "discriminating_experiment": "阻害剤を用いた直接作用の検証",
            },
            {
                "id": "hyp_2",
                "hypothesis": f"{phenomenon}は間接的な補償機構による",
                "conflicts_with": ["hyp_1"],
                "discriminating_experiment": "下流シグナルのタイムコース解析",
            },
        ]

    hypotheses = []

    # Generate hypotheses based on biological axis variations
    immune_high = [v for v in relevant if v.biological_axis.immune_activation > 0.3]
    immune_low = [v for v in relevant if v.biological_axis.immune_activation < -0.3]

    if immune_high:
        hypotheses.append(
            {
                "id": "hyp_immune_active",
                "hypothesis": f"{phenomenon}は免疫活性化経路を介する",
                "conflicts_with": ["hyp_immune_suppress"],
                "discriminating_experiment": "T細胞活性化マーカーの測定",
                "supporting_papers": [v.paper_id for v in immune_high[:2]],
            }
        )

    if immune_low:
        hypotheses.append(
            {
                "id": "hyp_immune_suppress",
                "hypothesis": f"{phenomenon}は免疫抑制経路を介する",
                "conflicts_with": ["hyp_immune_active"],
                "discriminating_experiment": "制御性T細胞の解析",
                "supporting_papers": [v.paper_id for v in immune_low[:2]],
            }
        )

    # Tumor context based hypotheses
    tme_high = [v for v in relevant if v.biological_axis.tumor_context > 0.3]
    systemic = [v for v in relevant if v.biological_axis.tumor_context < -0.3]

    if tme_high:
        hypotheses.append(
            {
                "id": "hyp_tme",
                "hypothesis": f"{phenomenon}はTME局所で発生する",
                "conflicts_with": ["hyp_systemic"],
                "discriminating_experiment": "腫瘍組織 vs 末梢血比較",
                "supporting_papers": [v.paper_id for v in tme_high[:2]],
            }
        )

    if systemic:
        hypotheses.append(
            {
                "id": "hyp_systemic",
                "hypothesis": f"{phenomenon}は全身免疫系で発生する",
                "conflicts_with": ["hyp_tme"],
                "discriminating_experiment": "脾臓・リンパ節解析",
                "supporting_papers": [v.paper_id for v in systemic[:2]],
            }
        )

    # Ensure at least 2 hypotheses
    if len(hypotheses) < 2:
        hypotheses.append(
            {
                "id": "hyp_metabolic",
                "hypothesis": f"{phenomenon}は代謝経路変化に起因する",
                "conflicts_with": [h["id"] for h in hypotheses],
                "discriminating_experiment": "メタボローム解析",
            }
        )

    return hypotheses