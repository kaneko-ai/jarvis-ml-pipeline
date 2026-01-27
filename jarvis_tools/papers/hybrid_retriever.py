"""Hybrid Retriever.

Per RP-119, combines BM25 and vector scores for retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional


@dataclass
class RetrievalResult:
    """A retrieval result with combined score."""

    doc_id: str
    bm25_score: float
    vector_score: float
    combined_score: float
    source: str  # bm25, vector, hybrid

    @property
    def scores(self) -> dict:
        return {
            "bm25": self.bm25_score,
            "vector": self.vector_score,
            "combined": self.combined_score,
        }


@dataclass
class HybridConfig:
    """Configuration for hybrid retrieval."""

    bm25_weight: float = 0.5
    vector_weight: float = 0.5
    normalize: bool = True
    min_score: float = 0.0


def normalize_scores(scores: List[float]) -> List[float]:
    """Normalize scores to [0, 1] range."""
    if not scores:
        return []

    min_s = min(scores)
    max_s = max(scores)

    if max_s == min_s:
        return [0.5] * len(scores)

    return [(s - min_s) / (max_s - min_s) for s in scores]


def hybrid_score(
    bm25_results: List[Tuple[str, float]],
    vector_results: List[Tuple[str, float]],
    config: Optional[HybridConfig] = None,
) -> List[RetrievalResult]:
    """Combine BM25 and vector retrieval results.

    Args:
        bm25_results: List of (doc_id, score) from BM25.
        vector_results: List of (doc_id, score) from vector search.
        config: Hybrid configuration.

    Returns:
        Combined results sorted by combined score.
    """
    if config is None:
        config = HybridConfig()

    # Build score maps
    bm25_map = {doc_id: score for doc_id, score in bm25_results}
    vector_map = {doc_id: score for doc_id, score in vector_results}

    # Get all doc IDs
    all_docs = set(bm25_map.keys()) | set(vector_map.keys())

    # Normalize if needed
    if config.normalize:
        bm25_scores = list(bm25_map.values())
        vector_scores = list(vector_map.values())

        if bm25_scores:
            bm25_norm = normalize_scores(bm25_scores)
            bm25_map = dict(zip(bm25_map.keys(), bm25_norm))

        if vector_scores:
            vector_norm = normalize_scores(vector_scores)
            vector_map = dict(zip(vector_map.keys(), vector_norm))

    # Combine scores
    results = []
    for doc_id in all_docs:
        bm25_s = bm25_map.get(doc_id, 0.0)
        vector_s = vector_map.get(doc_id, 0.0)

        combined = config.bm25_weight * bm25_s + config.vector_weight * vector_s

        # Determine source
        if doc_id in bm25_map and doc_id in vector_map:
            source = "hybrid"
        elif doc_id in bm25_map:
            source = "bm25"
        else:
            source = "vector"

        if combined >= config.min_score:
            results.append(
                RetrievalResult(
                    doc_id=doc_id,
                    bm25_score=bm25_s,
                    vector_score=vector_s,
                    combined_score=combined,
                    source=source,
                )
            )

    # Sort by combined score descending
    results.sort(key=lambda r: r.combined_score, reverse=True)

    return results


class HybridRetriever:
    """Hybrid retriever combining BM25 and vector search."""

    def __init__(
        self,
        bm25_fn: Callable[[str, int], List[Tuple[str, float]]],
        vector_fn: Optional[Callable[[str, int], List[Tuple[str, float]]]] = None,
        config: Optional[HybridConfig] = None,
    ):
        self.bm25_fn = bm25_fn
        self.vector_fn = vector_fn
        self.config = config or HybridConfig()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        use_vector: bool = True,
    ) -> List[RetrievalResult]:
        """Retrieve documents using hybrid scoring."""
        # Get BM25 results
        bm25_results = self.bm25_fn(query, top_k * 2)

        # Get vector results if enabled and available
        vector_results = []
        if use_vector and self.vector_fn is not None:
            try:
                vector_results = self.vector_fn(query, top_k * 2)
            except Exception:
                # Fallback to BM25 only
                pass

        # Combine
        combined = hybrid_score(bm25_results, vector_results, self.config)

        return combined[:top_k]
