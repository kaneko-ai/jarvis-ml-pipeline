"""Hypothesis Generator.

Per RP32, this detects gaps in literature and proposes hypotheses.
"""
from __future__ import annotations

from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def _find_concept_gaps(
    vectors: List["PaperVector"],
    focus_concepts: List[str],
) -> Dict[str, Dict[str, float]]:
    """Find which axes are understudied for each concept."""
    gaps = {}

    for concept in focus_concepts:
        # Find papers with this concept
        relevant = [v for v in vectors if concept in v.concept.concepts]

        if not relevant:
            gaps[concept] = {"immune": 1.0, "metabolism": 1.0, "tumor": 1.0}
            continue

        # Average axis coverage
        immune_sum = sum(abs(v.biological_axis.immune_activation) for v in relevant)
        metab_sum = sum(abs(v.biological_axis.metabolism_signal) for v in relevant)
        tumor_sum = sum(abs(v.biological_axis.tumor_context) for v in relevant)

        n = len(relevant)
        # Gaps are where coverage is low
        gaps[concept] = {
            "immune": 1.0 - (immune_sum / n) if immune_sum else 1.0,
            "metabolism": 1.0 - (metab_sum / n) if metab_sum else 1.0,
            "tumor": 1.0 - (tumor_sum / n) if tumor_sum else 1.0,
        }

    return gaps


def generate_hypotheses(
    vectors: List["PaperVector"],
    focus_concepts: List[str],
) -> List[dict]:
    """Generate research hypotheses based on literature gaps.

    Args:
        vectors: List of PaperVectors.
        focus_concepts: Concepts to focus on.

    Returns:
        List of hypothesis dicts.
    """
    if not vectors or not focus_concepts:
        return []

    gaps = _find_concept_gaps(vectors, focus_concepts)
    hypotheses = []

    for concept, axis_gaps in gaps.items():
        # Find the biggest gap
        max_gap_axis = max(axis_gaps, key=axis_gaps.get)
        max_gap_value = axis_gaps[max_gap_axis]

        if max_gap_value < 0.5:
            continue  # Not enough gap

        # Find supporting papers
        relevant = [v for v in vectors if concept in v.concept.concepts]
        based_on = [v.paper_id for v in relevant[:3]]

        # Generate hypothesis
        axis_to_phrase = {
            "immune": "免疫制御メカニズム",
            "metabolism": "代謝経路",
            "tumor": "腫瘍微小環境",
        }

        hypothesis = f"{concept}の{axis_to_phrase[max_gap_axis]}における役割は未解明である可能性が高い"

        hypotheses.append({
            "hypothesis": hypothesis,
            "missing_axis": max_gap_axis,
            "confidence": round(max_gap_value, 2),
            "concept": concept,
            "based_on": based_on,
        })

    # Sort by confidence
    hypotheses.sort(key=lambda x: x["confidence"], reverse=True)

    return hypotheses
