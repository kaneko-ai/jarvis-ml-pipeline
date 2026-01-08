"""Timeline / Knowledge Evolution Tracker.

Per RP33, this visualizes knowledge evolution over time.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def build_timeline(
    vectors: list[PaperVector],
    concept: str,
) -> list[dict]:
    """Build timeline of knowledge evolution for a concept.

    Args:
        vectors: List of PaperVectors.
        concept: Concept to track.

    Returns:
        List of timeline entries sorted by year.
    """
    # Filter papers with this concept
    relevant = []
    for v in vectors:
        if concept in v.concept.concepts:
            relevant.append(v)

    # Sort by year
    relevant.sort(key=lambda v: v.metadata.year or 9999)

    entries = []
    for v in relevant:
        # Track axis evolution
        entry = {
            "year": v.metadata.year,
            "paper_id": v.paper_id,
            "concept_score": v.concept.concepts.get(concept, 0.0),
            "immune_activation": v.biological_axis.immune_activation,
            "metabolism_signal": v.biological_axis.metabolism_signal,
            "tumor_context": v.biological_axis.tumor_context,
            "novelty": v.temporal.novelty,
            "methods": list(v.method.methods.keys())[:3],
        }
        entries.append(entry)

    return entries


def summarize_evolution(timeline: list[dict]) -> str:
    """Summarize knowledge evolution from timeline.

    Args:
        timeline: Result from build_timeline.

    Returns:
        Human-readable summary.
    """
    if not timeline:
        return "データなし"

    if len(timeline) < 2:
        return "時系列データが不足"

    first = timeline[0]
    last = timeline[-1]

    summary_parts = []

    # Check axis shifts
    immune_shift = (last.get("immune_activation", 0) or 0) - (first.get("immune_activation", 0) or 0)
    tumor_shift = (last.get("tumor_context", 0) or 0) - (first.get("tumor_context", 0) or 0)

    if abs(immune_shift) > 0.3:
        direction = "活性化方向" if immune_shift > 0 else "抑制方向"
        summary_parts.append(f"免疫軸が{direction}にシフト")

    if abs(tumor_shift) > 0.3:
        direction = "TME局所" if tumor_shift > 0 else "全身系"
        summary_parts.append(f"研究フォーカスが{direction}に移行")

    # Year span
    first_year = first.get("year") or "不明"
    last_year = last.get("year") or "不明"
    summary_parts.insert(0, f"{first_year}〜{last_year}の{len(timeline)}論文を分析")

    return "。".join(summary_parts)
