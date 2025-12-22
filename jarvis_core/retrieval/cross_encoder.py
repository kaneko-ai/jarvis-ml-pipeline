"""Cross-Encoder Reranker.

Per RP-303, implements two-stage retrieval with cross-encoder reranking.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Any


@dataclass
class RerankedResult:
    """A reranked search result."""
    
    chunk_id: str
    text: str
    original_score: float
    reranked_score: float
    rank: int
    metadata: dict


class CrossEncoderReranker:
    """Cross-encoder reranker for two-stage retrieval.
    
    Per RP-303:
    - Takes top-100 from initial retrieval
    - Reranks with cross-encoder
    - Adjusts rerank count based on latency budget
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_rerank: int = 100,
        latency_budget_ms: float = 1000.0,
    ):
        self.model_name = model_name
        self.max_rerank = max_rerank
        self.latency_budget_ms = latency_budget_ms
        self._model = None
    
    def _load_model(self):
        """Lazy load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except ImportError:
                self._model = None
        return self._model
    
    def rerank(
        self,
        query: str,
        candidates: List[dict],
        top_k: int = 10,
    ) -> List[RerankedResult]:
        """Rerank candidates using cross-encoder.
        
        Args:
            query: The search query.
            candidates: List of candidate chunks with text and scores.
            top_k: Number of results to return.
            
        Returns:
            Reranked results.
        """
        if not candidates:
            return []
        
        # Limit candidates to max_rerank
        candidates = candidates[:self.max_rerank]
        
        # Get cross-encoder scores
        model = self._load_model()
        
        if model:
            pairs = [(query, c.get("text", "")) for c in candidates]
            scores = model.predict(pairs)
        else:
            # Fallback: use original scores
            scores = [c.get("score", 0.0) for c in candidates]
        
        # Combine with original scores
        scored = []
        for i, (candidate, ce_score) in enumerate(zip(candidates, scores)):
            orig_score = candidate.get("score", 0.0)
            # Weighted combination (cross-encoder weighted higher)
            combined = 0.7 * float(ce_score) + 0.3 * orig_score
            scored.append((candidate, orig_score, combined))
        
        # Sort by combined score
        scored.sort(key=lambda x: x[2], reverse=True)
        
        # Build results
        results = []
        for rank, (candidate, orig_score, rerank_score) in enumerate(scored[:top_k]):
            results.append(RerankedResult(
                chunk_id=candidate.get("chunk_id", str(rank)),
                text=candidate.get("text", ""),
                original_score=orig_score,
                reranked_score=rerank_score,
                rank=rank + 1,
                metadata=candidate.get("metadata", {}),
            ))
        
        return results
    
    def estimate_latency(self, num_candidates: int) -> float:
        """Estimate reranking latency in ms.
        
        Args:
            num_candidates: Number of candidates to rerank.
            
        Returns:
            Estimated latency in milliseconds.
        """
        # Rough estimate: ~10ms per candidate
        return num_candidates * 10.0
    
    def adaptive_rerank(
        self,
        query: str,
        candidates: List[dict],
        top_k: int = 10,
    ) -> List[RerankedResult]:
        """Rerank with automatic candidate count adjustment.
        
        Args:
            query: The search query.
            candidates: All candidates.
            top_k: Number of results to return.
            
        Returns:
            Reranked results within latency budget.
        """
        # Calculate max candidates within budget
        max_by_budget = int(self.latency_budget_ms / 10)
        actual_max = min(max_by_budget, self.max_rerank, len(candidates))
        
        # Ensure we have enough for top_k
        actual_max = max(actual_max, min(top_k * 2, len(candidates)))
        
        return self.rerank(query, candidates[:actual_max], top_k)


class TwoStageRetriever:
    """Two-stage retrieval with reranking.
    
    Stage 1: Fast retrieval (BM25 or dense)
    Stage 2: Cross-encoder reranking
    """
    
    def __init__(
        self,
        first_stage_retriever,
        reranker: CrossEncoderReranker,
        first_stage_k: int = 100,
    ):
        self.first_stage = first_stage_retriever
        self.reranker = reranker
        self.first_stage_k = first_stage_k
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[RerankedResult]:
        """Two-stage retrieval.
        
        Args:
            query: Search query.
            top_k: Final number of results.
            
        Returns:
            Reranked results.
        """
        # Stage 1: Fast retrieval
        candidates = self.first_stage.search(query, top_k=self.first_stage_k)
        
        # Stage 2: Rerank
        return self.reranker.adaptive_rerank(query, candidates, top_k)
