"""Cluster Map Builder.

Per V4-M03, this builds cluster maps for field overview.
"""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper_vector import PaperVector


def build_cluster_map(
    vectors: list[PaperVector],
    num_clusters: int = 5,
) -> dict:
    """Build cluster map from papers.

    Args:
        vectors: Papers to cluster.
        num_clusters: Target number of clusters.

    Returns:
        Cluster map with centroids and members.
    """
    if not vectors:
        return {"clusters": [], "total_papers": 0}

    # Simple concept-based clustering
    concept_to_papers = defaultdict(list)

    for v in vectors:
        top_concept = max(v.concept.concepts.items(), key=lambda x: x[1])[0] if v.concept.concepts else "other"
        concept_to_papers[top_concept].append(v)

    # Build clusters
    clusters = []
    for concept, papers in sorted(concept_to_papers.items(), key=lambda x: -len(x[1]))[:num_clusters]:
        # Calculate centroid (average positions)
        avg_novelty = sum(p.temporal.novelty for p in papers) / len(papers)
        avg_impact = sum(p.impact.future_potential for p in papers) / len(papers)

        # Find center paper
        center = min(papers, key=lambda p: abs(p.temporal.novelty - avg_novelty) + abs(p.impact.future_potential - avg_impact))

        clusters.append({
            "cluster_id": f"cluster_{len(clusters)}",
            "top_concept": concept,
            "paper_ids": [p.paper_id for p in papers],
            "size": len(papers),
            "centroid": {
                "novelty": round(avg_novelty, 3),
                "impact": round(avg_impact, 3),
            },
            "center_paper": center.paper_id,
            "concepts": list(set(c for p in papers for c in p.concept.concepts))[:5],
        })

    return {
        "clusters": clusters,
        "total_papers": len(vectors),
        "cluster_count": len(clusters),
    }


def get_cluster_summary(cluster_map: dict) -> str:
    """Generate summary of clusters."""
    lines = ["# クラスタサマリー", ""]

    for c in cluster_map["clusters"]:
        lines.append(f"## {c['top_concept']} ({c['size']}論文)")
        lines.append(f"- 中心論文: {c['center_paper']}")
        lines.append(f"- 主要概念: {', '.join(c['concepts'][:3])}")
        lines.append("")

    return "\n".join(lines)
