"""Cross-Field Innovation Engine.

Per Issue Ω-5, this detects cross-field innovation opportunities.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def find_cross_field_opportunities(
    vectors: list[PaperVector],
    min_concept_overlap: float = 0.1,
) -> list[dict]:
    """Find cross-field innovation opportunities.

    Identifies concept combinations rarely seen together.

    Args:
        vectors: PaperVectors to analyze.
        min_concept_overlap: Minimum overlap to consider.

    Returns:
        List of opportunity dicts.
    """
    if not vectors:
        return []

    # Build concept co-occurrence matrix
    cooccurrence = {}
    concept_papers = {}

    for v in vectors:
        concepts = list(v.concept.concepts.keys())
        for c in concepts:
            if c not in concept_papers:
                concept_papers[c] = set()
            concept_papers[c].add(v.paper_id)

        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1:]:
                pair = tuple(sorted([c1, c2]))
                cooccurrence[pair] = cooccurrence.get(pair, 0) + 1

    # Find rare combinations with high individual presence
    opportunities = []
    all_concepts = list(concept_papers.keys())

    for i, c1 in enumerate(all_concepts):
        for c2 in all_concepts[i + 1:]:
            pair = tuple(sorted([c1, c2]))
            cooc_count = cooccurrence.get(pair, 0)

            c1_count = len(concept_papers.get(c1, set()))
            c2_count = len(concept_papers.get(c2, set()))

            # Both concepts should be well-studied
            if c1_count < 2 or c2_count < 2:
                continue

            # But rarely combined
            expected = (c1_count * c2_count) / len(vectors)
            gap_score = 1 - (cooc_count / max(expected, 0.1))
            gap_score = max(0, min(1, gap_score))

            if gap_score > 0.5:
                # Generate "why not" reason
                why_not = _analyze_why_not_combined(c1, c2, vectors)

                opportunities.append({
                    "concepts": [c1, c2],
                    "innovation_score": round(gap_score, 3),
                    "c1_papers": c1_count,
                    "c2_papers": c2_count,
                    "combined_papers": cooc_count,
                    "why_not_combined": why_not,
                    "potential": f"{c1} × {c2}の組み合わせは未開拓",
                })

    # Sort by innovation score
    opportunities.sort(key=lambda x: x["innovation_score"], reverse=True)

    return opportunities[:10]


def _analyze_why_not_combined(c1: str, c2: str, vectors: list[PaperVector]) -> str:
    """Analyze why two concepts are rarely combined."""
    # Simple heuristics
    c1_immune = False
    c2_tumor = False
    c1_years = []
    c2_years = []

    for v in vectors:
        if c1 in v.concept.concepts:
            c1_immune = c1_immune or v.biological_axis.immune_activation > 0.3
            if v.metadata.year:
                c1_years.append(v.metadata.year)

        if c2 in v.concept.concepts:
            c2_tumor = c2_tumor or v.biological_axis.tumor_context > 0.3
            if v.metadata.year:
                c2_years.append(v.metadata.year)

    reasons = []

    # Check axis separation
    if c1_immune and not c2_tumor:
        reasons.append("研究分野（免疫/非免疫）の分離")

    # Check temporal gap
    if c1_years and c2_years:
        avg_c1 = sum(c1_years) / len(c1_years)
        avg_c2 = sum(c2_years) / len(c2_years)
        if abs(avg_c1 - avg_c2) > 5:
            reasons.append("研究時期のずれ")

    if not reasons:
        reasons.append("技術的障壁または視点の違い（推定）")

    return "、".join(reasons)


def suggest_bridge_experiments(
    opportunity: dict,
    vectors: list[PaperVector],
) -> list[str]:
    """Suggest experiments to bridge two fields."""
    c1, c2 = opportunity["concepts"]

    suggestions = [
        f"{c1}陽性細胞における{c2}発現解析",
        f"{c2}ノックダウン時の{c1}機能変化",
        f"{c1}/{c2}二重標識イメージング",
    ]

    return suggestions
