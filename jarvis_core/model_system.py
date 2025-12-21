"""Model System Suggestion Engine.

Per RP46, this suggests experimental model systems.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Common model systems by concept
CONCEPT_MODELS = {
    "PD-1": {
        "cell_lines": ["Jurkat", "293T-PD1"],
        "animal_models": ["C57BL/6", "PD-1 KO"],
    },
    "CD73": {
        "cell_lines": ["MDA-MB-231", "4T1"],
        "animal_models": ["CD73 KO", "C57BL/6"],
    },
    "T cell": {
        "cell_lines": ["Jurkat", "MOLT-4"],
        "animal_models": ["C57BL/6", "OT-I transgenic"],
    },
    "macrophage": {
        "cell_lines": ["THP-1", "RAW264.7"],
        "animal_models": ["C57BL/6"],
    },
    "tumor": {
        "cell_lines": ["B16F10", "MC38", "4T1"],
        "animal_models": ["BALB/c", "C57BL/6", "NSG"],
    },
    "NK cell": {
        "cell_lines": ["NK-92"],
        "animal_models": ["C57BL/6", "NK depleted"],
    },
}


def suggest_model_system(
    hypothesis: str,
    vectors: List["PaperVector"],
) -> dict:
    """Suggest model systems for hypothesis testing.

    Args:
        hypothesis: The hypothesis to test.
        vectors: PaperVectors for context.

    Returns:
        Model system suggestion dict.
    """
    if not hypothesis:
        return {
            "cell_lines": [],
            "animal_models": [],
            "reason": "仮説が不明",
        }

    hypothesis_lower = hypothesis.lower()

    # Collect suggestions from concepts
    cell_lines = set()
    animal_models = set()
    matched_concepts = []

    for concept, models in CONCEPT_MODELS.items():
        if concept.lower() in hypothesis_lower:
            matched_concepts.append(concept)
            cell_lines.update(models["cell_lines"])
            animal_models.update(models["animal_models"])

    # Also check from related papers
    for v in vectors:
        for c in v.concept.concepts:
            for concept in CONCEPT_MODELS:
                if concept.lower() in c.lower():
                    models = CONCEPT_MODELS[concept]
                    cell_lines.update(models["cell_lines"])
                    animal_models.update(models["animal_models"])
                    break

    # Check species from metadata
    species_suggestions = set()
    for v in vectors:
        for species in v.metadata.species:
            if "human" in species.lower():
                cell_lines.add("primary human cells")
            elif "mouse" in species.lower():
                animal_models.add("corresponding mouse model")

    # Generate reason
    if matched_concepts:
        reason = f"{', '.join(matched_concepts)}に関連したモデル系を推奨"
    else:
        reason = "一般的なモデル系を推奨"

    return {
        "cell_lines": list(cell_lines)[:5],
        "animal_models": list(animal_models)[:4],
        "reason": reason,
        "matched_concepts": matched_concepts,
    }
