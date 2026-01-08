"""Research Gap Scoring Engine.

Per RP39, this scores research gaps to identify promising areas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def score_research_gaps(
    vectors: list[PaperVector],
    concept: str,
    year_range: tuple[int, int] | None = None,
) -> list[dict]:
    """Score research gaps for a concept.

    Gap score formula:
        0.4 * (1 - density) + 0.3 * novelty + 0.3 * (1 - recency)

    Args:
        vectors: All PaperVectors.
        concept: Concept to analyze.
        year_range: Optional year filter.

    Returns:
        List of gap analysis results.
    """
    if not vectors or not concept:
        return []

    # Filter by year if specified
    filtered = vectors
    if year_range:
        filtered = [
            v for v in vectors
            if v.metadata.year and year_range[0] <= v.metadata.year <= year_range[1]
        ]

    if not filtered:
        return []

    # Find papers with this concept
    concept_lower = concept.lower()
    relevant = []
    for v in filtered:
        for c in v.concept.concepts:
            if concept_lower in c.lower():
                relevant.append(v)
                break

    if not relevant:
        # High gap score if concept not studied
        return [{
            "concept": concept,
            "gap_score": 0.9,
            "papers": [],
            "density": 0.0,
            "novelty": 0.0,
            "recency": 0.0,
            "reason": "このコンセプトに関する研究がほぼ存在しない",
        }]

    # Calculate metrics
    density = len(relevant) / len(filtered)

    # Novelty average
    novelty = sum(v.temporal.novelty for v in relevant) / len(relevant)

    # Recency: normalize years
    years = [v.metadata.year for v in relevant if v.metadata.year]
    if years:
        min_year, max_year = min(years), max(years)
        current_year = 2024
        avg_year = sum(years) / len(years)
        # Recency: how recent is the average year (0=old, 1=recent)
        if max_year > min_year:
            recency = (avg_year - 2000) / (current_year - 2000)
            recency = max(0, min(1, recency))
        else:
            recency = 0.5
    else:
        recency = 0.5

    # Gap score
    gap_score = 0.4 * (1 - density) + 0.3 * novelty + 0.3 * (1 - recency)
    gap_score = max(0, min(1, gap_score))

    # Generate reason
    reason_parts = []
    if density < 0.3:
        reason_parts.append("論文数が少ない")
    if novelty > 0.6:
        reason_parts.append("新規性が高い")
    if recency < 0.5:
        reason_parts.append("近年の研究が不足")

    reason = "、".join(reason_parts) if reason_parts else "標準的な研究密度"

    return [{
        "concept": concept,
        "gap_score": round(gap_score, 3),
        "papers": [v.paper_id for v in relevant],
        "density": round(density, 3),
        "novelty": round(novelty, 3),
        "recency": round(recency, 3),
        "reason": reason,
    }]
