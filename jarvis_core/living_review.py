"""Living Review Generator.

Per Issue Ω-8, this generates and updates living reviews.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def generate_living_review(
    vectors: list[PaperVector],
    topic: str,
) -> dict:
    """Generate a living review that can be updated.

    Args:
        vectors: PaperVectors as source.
        topic: Review topic.

    Returns:
        Living review structure.
    """
    if not vectors or not topic:
        return {
            "topic": topic,
            "sections": [],
            "generated_at": datetime.now().isoformat(),
            "version": 1,
        }

    # Filter relevant papers
    topic_lower = topic.lower()
    relevant = []
    for v in vectors:
        for c in v.concept.concepts:
            if topic_lower in c.lower() or c.lower() in topic_lower:
                relevant.append(v)
                break

    # Sort by year
    relevant.sort(key=lambda v: v.metadata.year or 0)

    # Build sections
    sections = []

    # Background section
    early_papers = [v for v in relevant if (v.metadata.year or 9999) <= 2018]
    sections.append({
        "title": "背景",
        "content": f"{topic}に関する初期研究 ({len(early_papers)}論文)",
        "papers": [v.paper_id for v in early_papers],
        "key_concepts": _extract_key_concepts(early_papers),
    })

    # Recent advances
    recent_papers = [v for v in relevant if (v.metadata.year or 0) >= 2020]
    sections.append({
        "title": "最近の進展",
        "content": f"2020年以降の研究動向 ({len(recent_papers)}論文)",
        "papers": [v.paper_id for v in recent_papers],
        "key_concepts": _extract_key_concepts(recent_papers),
    })

    # Methods overview
    all_methods = {}
    for v in relevant:
        for m in v.method.methods:
            all_methods[m] = all_methods.get(m, 0) + 1

    sections.append({
        "title": "主要手法",
        "content": f"{len(all_methods)}種の手法が使用",
        "methods": dict(sorted(all_methods.items(), key=lambda x: x[1], reverse=True)[:5]),
    })

    # Future directions
    from .gap_analysis import score_research_gaps
    gaps = score_research_gaps(vectors, topic)
    sections.append({
        "title": "今後の方向性",
        "content": "研究ギャップに基づく提言",
        "gaps": gaps[0] if gaps else {},
    })

    return {
        "topic": topic,
        "sections": sections,
        "total_papers": len(relevant),
        "year_range": (
            min((v.metadata.year for v in relevant if v.metadata.year), default=None),
            max((v.metadata.year for v in relevant if v.metadata.year), default=None),
        ),
        "generated_at": datetime.now().isoformat(),
        "version": 1,
    }


def _extract_key_concepts(papers: list[PaperVector]) -> list[str]:
    """Extract key concepts from papers."""
    concept_counts = {}
    for p in papers:
        for c in p.concept.concepts:
            concept_counts[c] = concept_counts.get(c, 0) + 1

    sorted_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)
    return [c[0] for c in sorted_concepts[:5]]


def update_living_review(
    existing: dict,
    new_vectors: list[PaperVector],
) -> dict:
    """Update an existing living review with new papers.

    Args:
        existing: Existing review.
        new_vectors: New papers to incorporate.

    Returns:
        Updated review.
    """
    topic = existing.get("topic", "")

    # Combine and regenerate
    # In practice, would merge intelligently
    updated = generate_living_review(new_vectors, topic)
    updated["version"] = existing.get("version", 1) + 1
    updated["previous_version_at"] = existing.get("generated_at")

    return updated
