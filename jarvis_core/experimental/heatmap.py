"""Concept Heatmap Generator.

Per RP43, this generates year x concept heatmaps.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def build_concept_heatmap(
    vectors: list[PaperVector],
) -> dict[str, dict[str, float]]:
    """Build concept heatmap by year.

    Args:
        vectors: PaperVectors to analyze.

    Returns:
        Dict mapping year -> concept -> normalized score.
    """
    if not vectors:
        return {}

    # Collect by year
    by_year = {}
    for v in vectors:
        year = v.metadata.year
        if year is None:
            continue

        year_str = str(year)
        if year_str not in by_year:
            by_year[year_str] = {}

        for concept, score in v.concept.concepts.items():
            by_year[year_str][concept] = by_year[year_str].get(concept, 0) + score

    # Normalize to 0-1
    for year_str, concepts in by_year.items():
        if concepts:
            max_score = max(concepts.values())
            if max_score > 0:
                by_year[year_str] = {c: round(s / max_score, 3) for c, s in concepts.items()}

    # Sort by year
    sorted_result = dict(sorted(by_year.items(), key=lambda x: x[0]))

    return sorted_result


def get_trending_concepts(
    heatmap: dict[str, dict[str, float]],
    top_k: int = 5,
) -> list[dict]:
    """Get trending concepts from heatmap.

    Args:
        heatmap: Result from build_concept_heatmap.
        top_k: Number of concepts to return.

    Returns:
        List of trending concept dicts.
    """
    if not heatmap:
        return []

    years = sorted(heatmap.keys())
    if len(years) < 2:
        return []

    # Compare recent vs old
    mid = len(years) // 2
    old_years = years[:mid]
    new_years = years[mid:]

    old_totals = {}
    new_totals = {}

    for y in old_years:
        for c, s in heatmap.get(y, {}).items():
            old_totals[c] = old_totals.get(c, 0) + s

    for y in new_years:
        for c, s in heatmap.get(y, {}).items():
            new_totals[c] = new_totals.get(c, 0) + s

    # Calculate growth
    trends = []
    all_concepts = set(old_totals.keys()) | set(new_totals.keys())

    for c in all_concepts:
        old_val = old_totals.get(c, 0)
        new_val = new_totals.get(c, 0)
        growth = new_val - old_val

        trends.append(
            {
                "concept": c,
                "growth": round(growth, 3),
                "recent_score": round(new_val, 3),
                "trend": "rising" if growth > 0.2 else ("falling" if growth < -0.2 else "stable"),
            }
        )

    trends.sort(key=lambda x: x["growth"], reverse=True)

    return trends[:top_k]