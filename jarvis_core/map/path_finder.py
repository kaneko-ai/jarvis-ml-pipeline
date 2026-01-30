"""Concept Path Finder.

Per V4-M05, this finds conceptual paths between papers.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def find_concept_path(
    paper1: PaperVector,
    paper2: PaperVector,
    all_papers: list[PaperVector],
    max_depth: int = 4,
) -> dict | None:
    """Find conceptual path between two papers.

    Args:
        paper1: Start paper.
        paper2: End paper.
        all_papers: All available papers.
        max_depth: Maximum path length.

    Returns:
        Path with explanation, or None if not found.
    """
    if paper1.paper_id == paper2.paper_id:
        return {"path": [paper1.paper_id], "concepts": [], "length": 0}

    # Build concept graph
    concept_to_papers = {}
    for p in all_papers:
        for c in p.concept.concepts:
            if c not in concept_to_papers:
                concept_to_papers[c] = []
            concept_to_papers[c].append(p.paper_id)

    # BFS to find path
    start_concepts = set(paper1.concept.concepts.keys())
    end_concepts = set(paper2.concept.concepts.keys())

    # Direct connection?
    common = start_concepts & end_concepts
    if common:
        return {
            "path": [paper1.paper_id, paper2.paper_id],
            "concepts": list(common)[:3],
            "length": 1,
            "explanation": f"共通概念 {list(common)[0]} で直接接続",
        }

    # BFS
    visited = {paper1.paper_id}
    queue = deque([(paper1.paper_id, [paper1.paper_id], [])])

    while queue:
        current_id, path, concepts = queue.popleft()

        if len(path) > max_depth:
            continue

        # Find current paper
        current = None
        for p in all_papers:
            if p.paper_id == current_id:
                current = p
                break

        if not current:
            continue

        current_concepts = set(current.concept.concepts.keys())

        # Check if we can reach paper2
        if current_concepts & end_concepts:
            connecting = list(current_concepts & end_concepts)[0]
            return {
                "path": path + [paper2.paper_id],
                "concepts": concepts + [connecting],
                "length": len(path),
                "explanation": f"概念経路: {' → '.join(concepts + [connecting])}",
            }

        # Expand via shared concepts
        for concept in current_concepts:
            for neighbor_id in concept_to_papers.get(concept, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append(
                        (
                            neighbor_id,
                            path + [neighbor_id],
                            concepts + [concept],
                        )
                    )

    return None  # No path found