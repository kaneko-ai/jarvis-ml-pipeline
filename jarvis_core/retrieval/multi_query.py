"""Multi-Query Fusion.

Per RP-309, generates query variations for coverage.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class FusedResult:
    """Result from multi-query fusion."""

    chunk_id: str
    text: str
    fused_score: float
    query_hits: int
    metadata: dict


class MultiQueryFusion:
    """Generates query variations and fuses results.

    Per RP-309:
    - Generates 3-5 query variations
    - Searches each variation
    - Fuses results using RRF
    """

    def __init__(
        self,
        num_variations: int = 3,
        rrf_k: int = 60,
        generator: Callable[[str], list[str]] | None = None,
    ):
        self.num_variations = num_variations
        self.rrf_k = rrf_k
        self.generator = generator

    def generate_variations(self, query: str) -> list[str]:
        """Generate query variations.

        Args:
            query: Original query.

        Returns:
            List of query variations.
        """
        if self.generator:
            return self.generator(query)

        return self._template_variations(query)

    def _template_variations(self, query: str) -> list[str]:
        """Generate variations using templates."""
        variations = [query]

        # Rephrasing templates
        templates = [
            f"Research on {query}",
            f"Studies about {query}",
            f"Mechanism of {query}",
            f"Role of {query} in disease",
            f"{query} therapeutic implications",
        ]

        for template in templates[: self.num_variations - 1]:
            variations.append(template)

        return variations

    def reciprocal_rank_fusion(
        self,
        result_sets: list[list[dict[str, Any]]],
    ) -> list[FusedResult]:
        """Fuse multiple result sets using RRF.

        Args:
            result_sets: List of result lists from different queries.

        Returns:
            Fused results sorted by RRF score.
        """
        scores: dict[str, float] = {}
        hits: dict[str, int] = {}
        chunks: dict[str, dict[str, Any]] = {}

        for results in result_sets:
            for rank, result in enumerate(results):
                chunk_id = result.get("chunk_id", str(id(result)))

                # RRF score contribution
                rrf_score = 1.0 / (self.rrf_k + rank + 1)
                scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score
                hits[chunk_id] = hits.get(chunk_id, 0) + 1

                # Store chunk info
                if chunk_id not in chunks:
                    chunks[chunk_id] = result

        # Build fused results
        fused = []
        for chunk_id, score in scores.items():
            chunk = chunks[chunk_id]
            fused.append(
                FusedResult(
                    chunk_id=chunk_id,
                    text=chunk.get("text", ""),
                    fused_score=score,
                    query_hits=hits[chunk_id],
                    metadata=chunk.get("metadata", {}),
                )
            )

        # Sort by fused score
        fused.sort(key=lambda x: x.fused_score, reverse=True)

        return fused

    def search(
        self,
        query: str,
        retriever: Callable[[str, int], list[dict[str, Any]]],
        top_k: int = 10,
        per_query_k: int = 20,
    ) -> list[FusedResult]:
        """Multi-query search with fusion.

        Args:
            query: Original query.
            retriever: Search function.
            top_k: Final number of results.
            per_query_k: Results per query variation.

        Returns:
            Fused results.
        """
        # Generate variations
        variations = self.generate_variations(query)

        # Search each variation
        result_sets = []
        for var in variations:
            results = retriever(var, per_query_k)
            result_sets.append(results)

        # Fuse results
        fused = self.reciprocal_rank_fusion(result_sets)

        return fused[:top_k]
