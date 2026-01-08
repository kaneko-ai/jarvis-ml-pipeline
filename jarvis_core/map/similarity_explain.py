"""Hybrid Similarity Explainer.

Per V4-M01, this explains why papers are similar.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def explain_similarity(
    paper1: PaperVector,
    paper2: PaperVector,
) -> dict:
    """Explain why two papers are similar.

    Args:
        paper1: First paper.
        paper2: Second paper.

    Returns:
        Similarity explanation with score and reasons.
    """
    reasons = []

    # Concept overlap
    concepts1 = set(paper1.concept.concepts.keys())
    concepts2 = set(paper2.concept.concepts.keys())
    concept_overlap = concepts1 & concepts2

    if concept_overlap:
        reasons.append({
            "type": "concept_overlap",
            "items": list(concept_overlap)[:5],
            "score": len(concept_overlap) / max(len(concepts1 | concepts2), 1),
        })

    # Method overlap
    methods1 = set(paper1.method.methods.keys())
    methods2 = set(paper2.method.methods.keys())
    method_overlap = methods1 & methods2

    if method_overlap:
        reasons.append({
            "type": "method_overlap",
            "items": list(method_overlap)[:5],
            "score": len(method_overlap) / max(len(methods1 | methods2), 1),
        })

    # Biological axis proximity
    axis_dist = abs(paper1.biological_axis.immune_activation - paper2.biological_axis.immune_activation)
    if axis_dist < 0.3:
        reasons.append({
            "type": "axis_proximity",
            "axis": "immune_activation",
            "distance": round(axis_dist, 2),
            "score": 1 - axis_dist,
        })

    # Calculate overall score
    if reasons:
        overall_score = sum(r.get("score", 0) for r in reasons) / len(reasons)
    else:
        overall_score = 0

    return {
        "paper1": paper1.paper_id,
        "paper2": paper2.paper_id,
        "similarity_score": round(overall_score, 3),
        "reasons": reasons,
        "explanation": _generate_explanation(reasons),
    }


def _generate_explanation(reasons: list[dict]) -> str:
    """Generate human-readable explanation."""
    if not reasons:
        return "類似性の根拠が見つかりませんでした。"

    parts = []
    for r in reasons:
        if r["type"] == "concept_overlap":
            parts.append(f"共通概念: {', '.join(r['items'][:3])}")
        elif r["type"] == "method_overlap":
            parts.append(f"共通手法: {', '.join(r['items'][:3])}")
        elif r["type"] == "axis_proximity":
            parts.append(f"{r['axis']}軸が近接")

    return "類似理由: " + "; ".join(parts)
