"""Local Neighborhood Query.

Per V4-M04, this provides fast neighborhood exploration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def calculate_distance(p1: PaperVector, p2: PaperVector) -> float:
    """Calculate distance between two papers."""
    # Concept overlap (inversed)
    c1 = set(p1.concept.concepts.keys())
    c2 = set(p2.concept.concepts.keys())
    if c1 or c2:
        concept_sim = len(c1 & c2) / len(c1 | c2)
    else:
        concept_sim = 0

    # Method overlap
    m1 = set(p1.method.methods.keys())
    m2 = set(p2.method.methods.keys())
    if m1 or m2:
        method_sim = len(m1 & m2) / len(m1 | m2)
    else:
        method_sim = 0

    # Axis distance
    axis_dist = abs(p1.biological_axis.immune_activation - p2.biological_axis.immune_activation)

    # Combined distance (lower = more similar)
    distance = 1 - (0.5 * concept_sim + 0.3 * method_sim + 0.2 * (1 - axis_dist))

    return round(distance, 3)


def query_neighborhood(
    center: PaperVector,
    all_papers: list[PaperVector],
    k: int = 10,
) -> list[dict]:
    """Query k nearest neighbors.

    Args:
        center: Center paper.
        all_papers: All papers to search.
        k: Number of neighbors.

    Returns:
        List of nearest neighbors with distances.
    """
    if not all_papers:
        return []

    neighbors = []
    for paper in all_papers:
        if paper.paper_id == center.paper_id:
            continue

        dist = calculate_distance(center, paper)
        neighbors.append(
            {
                "paper_id": paper.paper_id,
                "distance": dist,
                "shared_concepts": list(
                    set(center.concept.concepts.keys()) & set(paper.concept.concepts.keys())
                )[:3],
            }
        )

    # Sort by distance (ascending)
    neighbors.sort(key=lambda x: x["distance"])

    return neighbors[:k]


def expand_neighborhood(
    seeds: list[PaperVector],
    all_papers: list[PaperVector],
    depth: int = 1,
) -> list[str]:
    """Expand from seeds to discover related papers.

    Args:
        seeds: Starting papers.
        all_papers: All papers.
        depth: Expansion depth.

    Returns:
        List of discovered paper IDs.
    """
    discovered = set(p.paper_id for p in seeds)
    current = seeds

    for _ in range(depth):
        next_layer = []
        for paper in current:
            neighbors = query_neighborhood(paper, all_papers, k=3)
            for n in neighbors:
                if n["paper_id"] not in discovered:
                    discovered.add(n["paper_id"])
                    # Find the actual paper
                    for p in all_papers:
                        if p.paper_id == n["paper_id"]:
                            next_layer.append(p)
                            break
        current = next_layer

    return list(discovered)
