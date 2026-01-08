"""Two-Stage Retriever.

Per V4.2 Sprint 3, this provides cheap candidate retrieval + expensive rerank.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievalResult:
    """Result of two-stage retrieval."""

    candidates: list[Any]
    reranked: list[Any]
    stage1_count: int
    stage2_count: int
    rerank_skipped: bool


class TwoStageRetriever:
    """Two-stage retrieval: cheap candidates + optional expensive rerank."""

    def __init__(
        self,
        stage1_fn: Callable[[str, int], list[Any]],
        stage2_fn: Callable[[str, list[Any]], list[Any]] | None = None,
        stage1_k: int = 100,
        stage2_k: int = 20,
        budget_threshold: float = 0.5,
    ):
        """Initialize retriever.

        Args:
            stage1_fn: First stage retrieval (cheap, high recall).
            stage2_fn: Second stage rerank (expensive, high precision).
            stage1_k: Number of candidates from stage 1.
            stage2_k: Number of results after stage 2.
            budget_threshold: Minimum budget ratio to enable stage 2.
        """
        self.stage1_fn = stage1_fn
        self.stage2_fn = stage2_fn
        self.stage1_k = stage1_k
        self.stage2_k = stage2_k
        self.budget_threshold = budget_threshold

    def retrieve(
        self,
        query: str,
        budget_remaining: float = 1.0,
    ) -> RetrievalResult:
        """Retrieve with two stages.

        Args:
            query: Search query.
            budget_remaining: Remaining budget ratio (0-1).

        Returns:
            RetrievalResult with candidates and reranked.
        """
        from ..perf.trace_spans import end_span, start_span

        # Stage 1: Cheap retrieval
        span1 = start_span("retrieval:stage1")
        candidates = self.stage1_fn(query, self.stage1_k)
        end_span(span1, item_count=len(candidates))

        # Check if stage 2 should be skipped
        rerank_skipped = (
            self.stage2_fn is None
            or budget_remaining < self.budget_threshold
            or len(candidates) <= self.stage2_k
        )

        if rerank_skipped:
            # Skip rerank, return top candidates
            reranked = candidates[: self.stage2_k]
        else:
            # Stage 2: Expensive rerank
            span2 = start_span("retrieval:stage2_rerank")
            reranked = self.stage2_fn(query, candidates)[: self.stage2_k]
            end_span(span2, item_count=len(reranked))

        return RetrievalResult(
            candidates=candidates,
            reranked=reranked,
            stage1_count=len(candidates),
            stage2_count=len(reranked),
            rerank_skipped=rerank_skipped,
        )


def simple_bm25_stage1(query: str, k: int) -> list[dict[str, Any]]:
    """Simple BM25-like stage 1 retriever (placeholder)."""
    # In production, this would use actual BM25 index
    query_terms = set(query.lower().split())

    return [
        {"id": f"doc_{i}", "score": 0.5, "text": f"Document {i} content"}
        for i in range(min(k, 100))
    ]


def simple_rerank_stage2(query: str, candidates: list[Any]) -> list[Any]:
    """Simple reranking (placeholder)."""
    # In production, this would use cross-encoder or similar
    # Sort by existing score (placeholder)
    return sorted(
        candidates,
        key=lambda x: x.get("score", 0) if isinstance(x, dict) else 0,
        reverse=True,
    )


def create_default_retriever() -> TwoStageRetriever:
    """Create retriever with default stages."""
    return TwoStageRetriever(
        stage1_fn=simple_bm25_stage1,
        stage2_fn=simple_rerank_stage2,
    )
