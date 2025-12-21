"""Paper Comparison Engine.

Per RP30, this compares two papers and explains differences.
"""
from __future__ import annotations

import math
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def compare_papers(a: "PaperVector", b: "PaperVector") -> dict:
    """Compare two papers and explain differences.

    Args:
        a: First paper.
        b: Second paper.

    Returns:
        Comparison dict with overlaps, diffs, and summary.
    """
    # Concept overlap and diff
    concepts_a = set(a.concept.concepts.keys())
    concepts_b = set(b.concept.concepts.keys())

    concept_overlap = {
        k: (a.concept.concepts.get(k, 0), b.concept.concepts.get(k, 0))
        for k in concepts_a & concepts_b
    }
    concept_only_a = list(concepts_a - concepts_b)
    concept_only_b = list(concepts_b - concepts_a)

    # Method diff
    methods_a = set(a.method.methods.keys())
    methods_b = set(b.method.methods.keys())

    method_overlap = list(methods_a & methods_b)
    method_only_a = list(methods_a - methods_b)
    method_only_b = list(methods_b - methods_a)

    # Biological axis distance
    bio_a = a.biological_axis.as_tuple()
    bio_b = b.biological_axis.as_tuple()

    bio_distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(bio_a, bio_b)))

    axis_diff = {
        "immune_activation": round(a.biological_axis.immune_activation - b.biological_axis.immune_activation, 2),
        "metabolism_signal": round(a.biological_axis.metabolism_signal - b.biological_axis.metabolism_signal, 2),
        "tumor_context": round(a.biological_axis.tumor_context - b.biological_axis.tumor_context, 2),
    }

    # Generate summary
    summary_parts = []

    if axis_diff["immune_activation"] > 0.3:
        summary_parts.append("Aは免疫活性寄り")
    elif axis_diff["immune_activation"] < -0.3:
        summary_parts.append("Bは免疫活性寄り")

    if axis_diff["metabolism_signal"] > 0.3:
        summary_parts.append("Aはシグナル伝達重視")
    elif axis_diff["metabolism_signal"] < -0.3:
        summary_parts.append("Bはシグナル伝達重視")

    if axis_diff["tumor_context"] > 0.3:
        summary_parts.append("AはTME局所")
    elif axis_diff["tumor_context"] < -0.3:
        summary_parts.append("Bは全身系")

    if not summary_parts:
        summary_parts.append("両論文は類似した研究領域")

    summary = "、".join(summary_parts)

    return {
        "paper_a": a.paper_id,
        "paper_b": b.paper_id,
        "concept_overlap": concept_overlap,
        "concept_only_a": concept_only_a,
        "concept_only_b": concept_only_b,
        "method_overlap": method_overlap,
        "method_only_a": method_only_a,
        "method_only_b": method_only_b,
        "biological_axis_distance": round(bio_distance, 3),
        "axis_diff": axis_diff,
        "summary": summary,
    }
