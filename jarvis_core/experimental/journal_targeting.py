"""Journal Targeting Assistant.

Per RP34, this suggests journals based on paper attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Journal profiles (simplified)
JOURNAL_PROFILES = {
    "Nature Immunology": {
        "concepts": ["immunotherapy", "T cell", "immune"],
        "immune_bias": 0.8,
        "novelty_threshold": 0.7,
    },
    "Cancer Immunology Research": {
        "concepts": ["tumor", "TME", "cancer", "immunotherapy"],
        "tumor_bias": 0.7,
        "novelty_threshold": 0.5,
    },
    "Cell Metabolism": {
        "concepts": ["metabolism", "ATP", "Adenosine"],
        "metabolism_bias": 0.7,
        "novelty_threshold": 0.6,
    },
    "Journal of Immunology": {
        "concepts": ["immune", "T cell", "macrophage"],
        "immune_bias": 0.5,
        "novelty_threshold": 0.4,
    },
    "PNAS": {
        "concepts": [],  # General
        "novelty_threshold": 0.5,
    },
    "Scientific Reports": {
        "concepts": [],
        "novelty_threshold": 0.3,
    },
}


def suggest_journals(
    vectors: list[PaperVector],
    top_k: int = 5,
) -> list[dict]:
    """Suggest target journals based on paper attributes.

    Args:
        vectors: List of PaperVectors representing the research.
        top_k: Number of suggestions.

    Returns:
        List of journal suggestions with fit scores.
    """
    if not vectors:
        return []

    # Aggregate attributes from all vectors
    all_concepts = {}
    avg_immune = 0.0
    avg_tumor = 0.0
    avg_metab = 0.0
    avg_novelty = 0.0

    for v in vectors:
        for c, score in v.concept.concepts.items():
            all_concepts[c] = all_concepts.get(c, 0) + score
        avg_immune += v.biological_axis.immune_activation
        avg_tumor += v.biological_axis.tumor_context
        avg_metab += v.biological_axis.metabolism_signal
        avg_novelty += v.temporal.novelty

    n = len(vectors)
    avg_immune /= n
    avg_tumor /= n
    avg_metab /= n
    avg_novelty /= n

    suggestions = []

    for journal, profile in JOURNAL_PROFILES.items():
        fit_score = 0.0
        reasons = []

        # Concept match
        concept_match = sum(all_concepts.get(c, 0) for c in profile.get("concepts", []))
        if concept_match > 0:
            fit_score += min(concept_match / 3, 0.4)
            reasons.append("概念が一致")

        # Axis match
        if profile.get("immune_bias", 0) > 0:
            if avg_immune > 0.3:
                fit_score += 0.2
                reasons.append("免疫研究")

        if profile.get("tumor_bias", 0) > 0:
            if avg_tumor > 0.3:
                fit_score += 0.2
                reasons.append("腫瘍研究")

        if profile.get("metabolism_bias", 0) > 0:
            if avg_metab < -0.3:
                fit_score += 0.2
                reasons.append("代謝研究")

        # Novelty threshold
        novelty_threshold = profile.get("novelty_threshold", 0.5)
        if avg_novelty >= novelty_threshold:
            fit_score += 0.2
            reasons.append("新規性要件を満たす")

        suggestions.append(
            {
                "journal": journal,
                "fit_score": round(fit_score, 2),
                "reason": "、".join(reasons) if reasons else "一般投稿可能",
            }
        )

    # Sort by fit score
    suggestions.sort(key=lambda x: x["fit_score"], reverse=True)

    return suggestions[:top_k]