"""Graph Booster.

Per V4.2 Sprint 3, this boosts candidates using citation/neighbor graphs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Set


@dataclass
class BoostResult:
    """Result of graph boosting."""

    boosted: List[Any]
    bridge_papers: List[str]
    boost_scores: Dict[str, float]


class GraphBooster:
    """Boost retrieval using graph relationships."""

    def __init__(
        self,
        citation_graph: Dict[str, List[str]] = None,
        similarity_graph: Dict[str, List[str]] = None,
        citation_boost: float = 0.2,
        neighbor_boost: float = 0.1,
    ):
        """Initialize booster.

        Args:
            citation_graph: Paper ID -> cited paper IDs.
            similarity_graph: Paper ID -> similar paper IDs.
            citation_boost: Boost for cited papers.
            neighbor_boost: Boost for similar papers.
        """
        self.citation_graph = citation_graph or {}
        self.similarity_graph = similarity_graph or {}
        self.citation_boost = citation_boost
        self.neighbor_boost = neighbor_boost

    def find_bridge_papers(
        self,
        seed_ids: List[str],
    ) -> List[str]:
        """Find papers that bridge between seed papers.

        Args:
            seed_ids: Seed paper IDs.

        Returns:
            List of bridge paper IDs.
        """
        # Get all cited papers from seeds
        cited_by_seeds: Set[str] = set()
        for seed in seed_ids:
            cited_by_seeds.update(self.citation_graph.get(seed, []))

        # Find papers cited by multiple seeds (bridges)
        cite_counts: Dict[str, int] = {}
        for seed in seed_ids:
            for cited in self.citation_graph.get(seed, []):
                cite_counts[cited] = cite_counts.get(cited, 0) + 1

        bridges = [
            paper_id for paper_id, count in cite_counts.items()
            if count > 1 and paper_id not in seed_ids
        ]

        return bridges

    def boost(
        self,
        candidates: List[Any],
        seed_ids: List[str] = None,
    ) -> BoostResult:
        """Boost candidates using graph relationships.

        Args:
            candidates: Initial candidates with id and score.
            seed_ids: Optional seed paper IDs for context.

        Returns:
            BoostResult with boosted candidates.
        """
        seed_ids = seed_ids or []
        boost_scores: Dict[str, float] = {}
        bridge_papers = self.find_bridge_papers(seed_ids)

        # Calculate boosts
        for candidate in candidates:
            cid = candidate.get("id", "") if isinstance(candidate, dict) else str(candidate)
            boost = 0.0

            # Citation boost: if candidate cites or is cited by seeds
            for seed in seed_ids:
                if cid in self.citation_graph.get(seed, []):
                    boost += self.citation_boost
                if seed in self.citation_graph.get(cid, []):
                    boost += self.citation_boost * 0.5  # Reverse citation

            # Neighbor boost: if candidate is similar to seeds
            for seed in seed_ids:
                if cid in self.similarity_graph.get(seed, []):
                    boost += self.neighbor_boost

            # Bridge boost
            if cid in bridge_papers:
                boost += self.citation_boost * 1.5

            boost_scores[cid] = boost

        # Apply boosts
        boosted = []
        for candidate in candidates:
            if isinstance(candidate, dict):
                cid = candidate.get("id", "")
                new_score = candidate.get("score", 0) + boost_scores.get(cid, 0)
                boosted.append({**candidate, "score": new_score})
            else:
                boosted.append(candidate)

        # Sort by boosted score
        boosted.sort(
            key=lambda x: x.get("score", 0) if isinstance(x, dict) else 0,
            reverse=True,
        )

        return BoostResult(
            boosted=boosted,
            bridge_papers=bridge_papers,
            boost_scores=boost_scores,
        )
