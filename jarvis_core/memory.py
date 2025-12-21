"""Personal Research Memory (Cross-search).

Per RP37, this enables searching across past research assets.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def search_memory(
    vectors: List["PaperVector"],
    query: str,
    top_k: int = 10,
) -> List["PaperVector"]:
    """Search research memory for relevant papers.

    Searches across:
    - Concepts
    - Embeddings (if available)
    - Years (if query contains year)

    Args:
        vectors: All stored PaperVectors.
        query: Search query.
        top_k: Maximum results.

    Returns:
        List of matching PaperVectors.
    """
    if not vectors or not query:
        return []

    query_lower = query.lower()
    scored = []

    for v in vectors:
        score = 0.0

        # Concept matching
        for concept, c_score in v.concept.concepts.items():
            if concept.lower() in query_lower or query_lower in concept.lower():
                score += c_score * 2.0

        # Method matching
        for method in v.method.methods.keys():
            if method.lower() in query_lower:
                score += 0.5

        # Year matching
        import re
        year_match = re.search(r"\b(19|20)\d{2}\b", query)
        if year_match:
            year = int(year_match.group())
            if v.metadata.year == year:
                score += 1.0

        # Simple text matching in source
        if v.source_locator:
            source_lower = v.source_locator.lower()
            words = query_lower.split()
            for word in words:
                if len(word) > 3 and word in source_lower:
                    score += 0.3

        if score > 0:
            scored.append((score, v))

    # Sort by score
    scored.sort(key=lambda x: x[0], reverse=True)

    return [v for _, v in scored[:top_k]]


def find_related(
    paper: "PaperVector",
    all_vectors: List["PaperVector"],
    top_k: int = 5,
) -> List["PaperVector"]:
    """Find papers related to a given paper.

    Args:
        paper: The reference paper.
        all_vectors: All papers to search.
        top_k: Number of results.

    Returns:
        List of related PaperVectors.
    """
    scored = []

    for v in all_vectors:
        if v.paper_id == paper.paper_id:
            continue  # Skip self

        score = 0.0

        # Concept overlap
        for concept, c_score in paper.concept.concepts.items():
            if concept in v.concept.concepts:
                score += c_score * v.concept.concepts[concept]

        # Biological axis similarity
        import math
        ba_paper = paper.biological_axis.as_tuple()
        ba_v = v.biological_axis.as_tuple()
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(ba_paper, ba_v)))
        # Closer = higher score
        score += max(0, 2.0 - distance)

        if score > 0:
            scored.append((score, v))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [v for _, v in scored[:top_k]]


def get_memory_stats(vectors: List["PaperVector"]) -> dict:
    """Get statistics about the research memory.

    Args:
        vectors: All stored PaperVectors.

    Returns:
        Stats dict.
    """
    if not vectors:
        return {"total_papers": 0}

    years = [v.metadata.year for v in vectors if v.metadata.year]
    all_concepts = {}
    for v in vectors:
        for c, score in v.concept.concepts.items():
            all_concepts[c] = all_concepts.get(c, 0) + 1

    top_concepts = sorted(all_concepts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_papers": len(vectors),
        "year_range": (min(years), max(years)) if years else None,
        "top_concepts": top_concepts,
        "unique_concepts": len(all_concepts),
    }
