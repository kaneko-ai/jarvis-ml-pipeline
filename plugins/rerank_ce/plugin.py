"""
JARVIS Rerank Plugin - CrossEncoder Reranker

検索結果の精密リランキング。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, RuntimeConfig, TaskContext
)


@dataclass
class RerankResult:
    """リランク結果."""
    doc_id: str
    chunk_id: str
    original_score: float
    rerank_score: float
    text: str


class CrossEncoderReranker:
    """
    CrossEncoderによるリランク.
    
    クエリと文書のペアを直接スコアリング。
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None

        # Try to load CrossEncoder
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
        except ImportError:
            pass

    def rerank(self, query: str,
               candidates: List[Tuple[str, str, str, float]],
               top_k: int = 10) -> List[RerankResult]:
        """
        候補をリランク.
        
        Args:
            query: クエリ
            candidates: [(doc_id, chunk_id, text, original_score), ...]
            top_k: 返す件数
        
        Returns:
            リランク結果
        """
        if not candidates:
            return []

        if self.model:
            return self._rerank_with_model(query, candidates, top_k)
        else:
            return self._rerank_simple(query, candidates, top_k)

    def _rerank_with_model(self, query: str,
                           candidates: List[Tuple[str, str, str, float]],
                           top_k: int) -> List[RerankResult]:
        """CrossEncoderでリランク."""
        pairs = [(query, c[2]) for c in candidates]
        scores = self.model.predict(pairs)

        results = []
        for i, (doc_id, chunk_id, text, orig_score) in enumerate(candidates):
            results.append(RerankResult(
                doc_id=doc_id,
                chunk_id=chunk_id,
                original_score=orig_score,
                rerank_score=float(scores[i]),
                text=text[:500]
            ))

        results.sort(key=lambda x: x.rerank_score, reverse=True)
        return results[:top_k]

    def _rerank_simple(self, query: str,
                       candidates: List[Tuple[str, str, str, float]],
                       top_k: int) -> List[RerankResult]:
        """簡易リランク（キーワードマッチング）."""
        query_words = set(query.lower().split())

        results = []
        for doc_id, chunk_id, text, orig_score in candidates:
            text_words = set(text.lower().split())

            # Keyword overlap score
            overlap = len(query_words & text_words)
            rerank_score = orig_score * (1 + overlap * 0.1)

            results.append(RerankResult(
                doc_id=doc_id,
                chunk_id=chunk_id,
                original_score=orig_score,
                rerank_score=rerank_score,
                text=text[:500]
            ))

        results.sort(key=lambda x: x.rerank_score, reverse=True)
        return results[:top_k]


class RerankPlugin:
    """Rerank Plugin."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.reranker = CrossEncoderReranker(model_name)
        self.is_active = False

    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        self.is_active = True

    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """リランクを実行."""
        delta: ArtifactsDelta = {}

        # Get search results from artifacts metadata
        search_results = artifacts.metadata.get("search_results", [])

        if not search_results:
            return delta

        # Prepare candidates
        candidates = []
        for r in search_results:
            doc_id = r.get("doc_id", "")
            chunk_id = r.get("chunk_id", "")
            score = r.get("score", 0.0)

            # Get text from chunks
            text = artifacts.chunks.get(doc_id, {}).get(chunk_id, "")
            if text:
                candidates.append((doc_id, chunk_id, text, score))

        # Rerank
        results = self.reranker.rerank(context.goal, candidates, top_k=20)

        delta["reranked_results"] = [
            {
                "doc_id": r.doc_id,
                "chunk_id": r.chunk_id,
                "original_score": r.original_score,
                "rerank_score": r.rerank_score
            }
            for r in results
        ]

        return delta

    def deactivate(self) -> None:
        self.is_active = False


def get_rerank_plugin() -> RerankPlugin:
    return RerankPlugin()
