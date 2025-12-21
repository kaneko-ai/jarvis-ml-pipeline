"""Paradigm Shift Detector.

Per RP41, this detects paradigm shifts in research fields.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def detect_paradigm_shift(
    vectors: List["PaperVector"],
    concept: str,
) -> dict | None:
    """Detect paradigm shifts for a concept.

    Args:
        vectors: PaperVectors to analyze.
        concept: Concept to track.

    Returns:
        Shift info dict or None if no shift detected.
    """
    if not vectors or not concept:
        return None

    # Find papers with this concept
    concept_lower = concept.lower()
    relevant = []
    for v in vectors:
        if v.metadata.year is None:
            continue
        for c in v.concept.concepts:
            if concept_lower in c.lower():
                relevant.append(v)
                break

    if len(relevant) < 3:
        return None

    # Sort by year
    relevant.sort(key=lambda v: v.metadata.year)

    # Group by year
    by_year = {}
    for v in relevant:
        year = v.metadata.year
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(v)

    years = sorted(by_year.keys())
    if len(years) < 2:
        return None

    # Detect method shift
    best_shift = None
    max_shift_score = 0.3  # Threshold

    for i in range(len(years) - 1):
        year_a = years[i]
        year_b = years[i + 1]

        papers_a = by_year[year_a]
        papers_b = by_year[year_b]

        # Count methods
        methods_a = {}
        for p in papers_a:
            for m in p.method.methods:
                methods_a[m] = methods_a.get(m, 0) + 1

        methods_b = {}
        for p in papers_b:
            for m in p.method.methods:
                methods_b[m] = methods_b.get(m, 0) + 1

        # Find new emerging methods
        emerging = set(methods_b.keys()) - set(methods_a.keys())
        disappearing = set(methods_a.keys()) - set(methods_b.keys())

        shift_score = (len(emerging) + len(disappearing)) / max(len(methods_a) + len(methods_b), 1)

        if shift_score > max_shift_score:
            max_shift_score = shift_score
            evidence_parts = []
            if emerging:
                evidence_parts.append(f"新手法出現: {', '.join(list(emerging)[:2])}")
            if disappearing:
                evidence_parts.append(f"手法衰退: {', '.join(list(disappearing)[:2])}")

            best_shift = {
                "year": year_b,
                "evidence": "; ".join(evidence_parts) if evidence_parts else "手法の変化を検出",
                "shift_score": round(shift_score, 3),
            }

    return best_shift
