"""ITER-08: ハイブリッド検索固定 (Hybrid Search).

BM25 + ベクトル検索のハイブリッド。
- スコア正規化
- 重み調整
- Reciprocal Rank Fusion
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HybridSearchResult:
    """ハイブリッド検索結果."""

    chunk_id: str
    paper_id: str
    text: str
    bm25_score: float = 0.0
    vector_score: float = 0.0
    hybrid_score: float = 0.0
    rank: int = 0

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "bm25_score": self.bm25_score,
            "vector_score": self.vector_score,
            "hybrid_score": self.hybrid_score,
            "rank": self.rank,
        }


class HybridSearchEngine:
    """ハイブリッド検索エンジン.

    BM25とベクトル検索を組み合わせ。
    """

    def __init__(
        self,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k
        self._bm25_engine = None
        self._vector_store = None

    def search(
        self,
        query: str,
        top_k: int = 20,
        method: str = "weighted",  # weighted, rrf
    ) -> list[HybridSearchResult]:
        """ハイブリッド検索.

        Args:
            query: 検索クエリ
            top_k: 上位k件
            method: 結合方法（weighted=重み付き、rrf=RRF）

        Returns:
            結果リスト
        """
        # BM25検索
        from jarvis_core.search import get_search_engine

        bm25 = get_search_engine()
        bm25_results = bm25.search(query, top_k=top_k * 2)

        # ベクトル検索（利用可能な場合）
        vector_results = self._vector_search(query, top_k * 2)

        if method == "rrf":
            return self._reciprocal_rank_fusion(bm25_results, vector_results, top_k)
        else:
            return self._weighted_combination(bm25_results, vector_results, top_k)

    def _vector_search(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """ベクトル検索（スタブ）."""
        # TODO: 実際のベクトル検索実装
        return []

    def _weighted_combination(
        self,
        bm25_results: Any,
        vector_results: list[dict[str, Any]],
        top_k: int,
    ) -> list[HybridSearchResult]:
        """重み付き結合."""
        # スコアを正規化して結合
        combined = {}

        # BM25結果を追加
        if hasattr(bm25_results, "results"):
            max_bm25 = max((r.score for r in bm25_results.results), default=1)
            for r in bm25_results.results:
                chunk_id = r.chunk_id
                normalized = r.score / max_bm25 if max_bm25 > 0 else 0
                combined[chunk_id] = HybridSearchResult(
                    chunk_id=chunk_id,
                    paper_id=r.paper_id,
                    text=r.text,
                    bm25_score=normalized,
                    vector_score=0.0,
                    hybrid_score=normalized * self.bm25_weight,
                )

        # ベクトル結果を結合
        if vector_results:
            max_vec = max((r.get("score", 0) for r in vector_results), default=1)
            for r in vector_results:
                chunk_id = r.get("chunk_id", "")
                normalized = r.get("score", 0) / max_vec if max_vec > 0 else 0

                if chunk_id in combined:
                    combined[chunk_id].vector_score = normalized
                    combined[chunk_id].hybrid_score += normalized * self.vector_weight
                else:
                    combined[chunk_id] = HybridSearchResult(
                        chunk_id=chunk_id,
                        paper_id=r.get("paper_id", ""),
                        text=r.get("text", ""),
                        bm25_score=0.0,
                        vector_score=normalized,
                        hybrid_score=normalized * self.vector_weight,
                    )

        # ソートとランク付け
        results = sorted(combined.values(), key=lambda x: x.hybrid_score, reverse=True)[:top_k]
        for i, r in enumerate(results):
            r.rank = i + 1

        return results

    def _reciprocal_rank_fusion(
        self,
        bm25_results: Any,
        vector_results: list[dict[str, Any]],
        top_k: int,
    ) -> list[HybridSearchResult]:
        """Reciprocal Rank Fusion.

        RRF(d) = Σ 1 / (k + rank(d))
        """
        rrf_scores: dict[str, float] = {}
        chunk_data: dict[str, dict[str, Any]] = {}

        # BM25ランク
        if hasattr(bm25_results, "results"):
            for rank, r in enumerate(bm25_results.results, 1):
                chunk_id = r.chunk_id
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (self.rrf_k + rank)
                chunk_data[chunk_id] = {
                    "paper_id": r.paper_id,
                    "text": r.text,
                    "bm25_score": r.score,
                }

        # ベクトルランク
        for rank, r in enumerate(vector_results, 1):
            chunk_id = r.get("chunk_id", "")
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (self.rrf_k + rank)
            if chunk_id not in chunk_data:
                chunk_data[chunk_id] = {
                    "paper_id": r.get("paper_id", ""),
                    "text": r.get("text", ""),
                    "bm25_score": 0,
                }
            chunk_data[chunk_id]["vector_score"] = r.get("score", 0)

        # 結果生成
        results = []
        for chunk_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            data = chunk_data.get(chunk_id, {})
            results.append(
                HybridSearchResult(
                    chunk_id=chunk_id,
                    paper_id=data.get("paper_id", ""),
                    text=data.get("text", ""),
                    bm25_score=data.get("bm25_score", 0),
                    vector_score=data.get("vector_score", 0),
                    hybrid_score=score,
                )
            )

        for i, r in enumerate(results):
            r.rank = i + 1

        return results


def hybrid_search(
    query: str,
    top_k: int = 20,
    bm25_weight: float = 0.5,
) -> list[HybridSearchResult]:
    """便利関数: ハイブリッド検索."""
    engine = HybridSearchEngine(bm25_weight=bm25_weight, vector_weight=1 - bm25_weight)
    return engine.search(query, top_k)