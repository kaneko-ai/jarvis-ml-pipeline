"""Bridge Paper Finder.

Per V4-M02, this finds papers that connect clusters.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def find_bridge_papers(
    cluster1: List["PaperVector"],
    cluster2: List["PaperVector"],
    all_papers: List["PaperVector"],
) -> List[dict]:
    """Find papers that bridge two clusters.

    Args:
        cluster1: First cluster of papers.
        cluster2: Second cluster of papers.
        all_papers: All available papers.

    Returns:
        List of bridge paper candidates.
    """
    if not cluster1 or not cluster2:
        return []

    # Get concepts from each cluster
    concepts1 = set()
    for p in cluster1:
        concepts1.update(p.concept.concepts.keys())

    concepts2 = set()
    for p in cluster2:
        concepts2.update(p.concept.concepts.keys())

    # Find papers in neither cluster that share concepts with both
    cluster_ids = {p.paper_id for p in cluster1} | {p.paper_id for p in cluster2}

    bridges = []
    for paper in all_papers:
        if paper.paper_id in cluster_ids:
            continue

        paper_concepts = set(paper.concept.concepts.keys())
        overlap1 = paper_concepts & concepts1
        overlap2 = paper_concepts & concepts2

        if overlap1 and overlap2:
            bridge_score = (len(overlap1) + len(overlap2)) / len(paper_concepts) if paper_concepts else 0
            bridges.append({
                "paper_id": paper.paper_id,
                "bridge_score": round(bridge_score, 3),
                "connects_concepts_1": list(overlap1)[:3],
                "connects_concepts_2": list(overlap2)[:3],
                "reason": f"Bridges {list(overlap1)[0]} ↔ {list(overlap2)[0]}",
            })

    # Sort by bridge score
    bridges.sort(key=lambda x: x["bridge_score"], reverse=True)

    return bridges[:10]
