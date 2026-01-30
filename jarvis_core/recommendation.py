"""Paper Recommendation Engine.

Per RP29, this recommends papers based on multi-attribute vectors.
Uses concept similarity, novelty, and future potential.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def _concept_similarity(a: dict[str, float], b: list[str]) -> float:
    """Calculate similarity between concepts dict and target concepts."""
    if not b:
        return 0.0

    total = 0.0
    for concept in b:
        total += a.get(concept, 0.0)

    return min(total / len(b), 1.0)


def recommend_papers(
    vectors: list[PaperVector],
    target_concepts: list[str],
    year_range: tuple[int, int] | None = None,
    top_k: int = 10,
) -> list[dict]:
    """Recommend papers based on concepts and attributes.

    Score formula:
        0.6 * concept_similarity +
        0.2 * temporal.novelty +
        0.2 * impact.future_potential

    Args:
        vectors: List of PaperVectors to search.
        target_concepts: Concepts to match.
        year_range: Optional (min_year, max_year) filter.
        top_k: Number of results.

    Returns:
        List of recommendation dicts with score and reason.
    """
    if not vectors:
        return []

    scored = []

    for pv in vectors:
        # Year filter
        if year_range is not None:
            year = pv.metadata.year
            if year is None:
                continue
            if year < year_range[0] or year > year_range[1]:
                continue

        # Calculate score components
        concept_sim = _concept_similarity(pv.concept.concepts, target_concepts)
        novelty = pv.temporal.novelty
        future_pot = pv.impact.future_potential

        score = 0.6 * concept_sim + 0.2 * novelty + 0.2 * future_pot

        # Generate reason
        top_concepts = pv.concept.top_concepts(3)
        concept_names = [c[0] for c in top_concepts if c[1] > 0.3]

        reason_parts = []
        if concept_names:
            reason_parts.append(f"{', '.join(concept_names)}に関連")
        if novelty > 0.6:
            reason_parts.append("新規性が高い")
        if future_pot > 0.6:
            reason_parts.append("発展余地が大きい")

        reason = "。".join(reason_parts) if reason_parts else "関連論文"

        scored.append(
            {
                "paper_id": pv.paper_id,
                "source_locator": pv.source_locator,
                "score": round(score, 3),
                "reason": reason,
                "year": pv.metadata.year,
            }
        )

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:top_k]
