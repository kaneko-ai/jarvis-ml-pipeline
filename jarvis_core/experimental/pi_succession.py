"""PI Succession Planner.

Per Ψ-9, this plans lab succession strategy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def plan_pi_succession(
    current_vectors: list[PaperVector],
    lab_age_years: int = 10,
) -> dict:
    """Plan PI succession and future theme map.

    Args:
        current_vectors: Current lab's PaperVectors.
        lab_age_years: How long the lab has existed.

    Returns:
        Succession planning with future theme map.
    """
    if not current_vectors:
        return {
            "future_theme_map": [],
            "succession_readiness": "low",
            "estimated": True,
        }

    # Analyze current strengths
    concept_scores = {}
    for v in current_vectors:
        for c, score in v.concept.concepts.items():
            concept_scores[c] = concept_scores.get(c, 0) + score

    # Top themes to preserve
    top_themes = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)[:5]

    # Analyze emerging vs established
    recent = [v for v in current_vectors if (v.metadata.year or 0) >= 2022]
    recent_concepts = set()
    for v in recent:
        recent_concepts.update(v.concept.concepts.keys())

    established_concepts = set(concept_scores.keys()) - recent_concepts

    # Build future theme map
    future_theme_map = []

    for concept, score in top_themes[:3]:
        theme = {
            "theme": concept,
            "strength": round(score, 2),
            "status": "established" if concept in established_concepts else "emerging",
            "recommendation": (
                "次世代継承推奨" if concept in established_concepts else "発展途上、要育成"
            ),
        }
        future_theme_map.append(theme)

    # Succession readiness
    if len(established_concepts) >= 2 and len(recent) >= 3:
        readiness = "high"
    elif len(established_concepts) >= 1:
        readiness = "medium"
    else:
        readiness = "low"

    return {
        "future_theme_map": future_theme_map,
        "succession_readiness": readiness,
        "established_themes": len(established_concepts),
        "emerging_themes": len(recent_concepts),
        "lab_age_years": lab_age_years,
        "estimated": True,
    }