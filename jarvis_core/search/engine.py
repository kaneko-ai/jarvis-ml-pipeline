"""Search API (AG-09).

BM25/ハイブリッド検索API。
チャンクを対象にlocator付き検索結果を返す。
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SearchResult:
    """検索結果."""

    chunk_id: str
    paper_id: str
    paper_title: str
    text: str
    score: float
    locator: dict[str, Any]
    highlights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "paper_title": self.paper_title,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "score": self.score,
            "locator": self.locator,
            "highlights": self.highlights,
        }


@dataclass
class SearchResults:
    """検索結果群."""

    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    query: str = ""
    took_ms: float = 0

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "query": self.query,
            "took_ms": self.took_ms,
        }


class BM25Index:
    """BM25インデックス."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: list[dict[str, Any]] = []
        self.doc_freqs: Counter = Counter()
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0
        self.num_docs: int = 0

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        """ドキュメントを追加."""
        for doc in documents:
            text = doc.get("text", "")
            tokens = self._tokenize(text)

            self.documents.append(doc)
            self.doc_lengths.append(len(tokens))

            # 文書頻度をカウント
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1

        self.num_docs = len(self.documents)
        self.avg_doc_length = sum(self.doc_lengths) / max(1, self.num_docs)

    def search(self, query: str, top_k: int = 10) -> list[tuple]:
        """検索.

        Returns:
            [(doc_index, score), ...]
        """
        query_tokens = self._tokenize(query)
        scores = []

        for doc_idx, doc in enumerate(self.documents):
            text = doc.get("text", "")
            doc_tokens = self._tokenize(text)
            doc_len = self.doc_lengths[doc_idx]

            score = self._compute_bm25(query_tokens, doc_tokens, doc_len)
            scores.append((doc_idx, score))

        # スコア順にソート
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]

    def _compute_bm25(
        self,
        query_tokens: list[str],
        doc_tokens: list[str],
        doc_len: int,
    ) -> float:
        """BM25スコアを計算."""
        score = 0.0
        doc_token_counts = Counter(doc_tokens)

        for token in query_tokens:
            if token not in doc_token_counts:
                continue

            tf = doc_token_counts[token]
            df = self.doc_freqs.get(token, 0)

            # IDF
            idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1)

            # TF正規化
            norm = self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
            tf_normalized = (tf * (self.k1 + 1)) / (tf + norm)

            score += idf * tf_normalized

        return score

    def _tokenize(self, text: str) -> list[str]:
        """トークン化."""
        text = text.lower()
        tokens = re.findall(r"\b[a-z][a-z0-9]+\b", text)
        return tokens


class SearchEngine:
    """検索エンジン.

    BM25ベースの検索 + 将来的なベクトル検索拡張。
    """

    def __init__(self):
        self.bm25 = BM25Index()
        self._chunks: list[dict[str, Any]] = []
        self._loaded = False

    def load_chunks(self, filepath: Path) -> int:
        """chunks.jsonlを読み込み."""
        self._chunks = []

        if not filepath.exists():
            return 0

        with open(filepath, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self._chunks.append(json.loads(line))

        self.bm25.add_documents(self._chunks)
        self._loaded = True

        return len(self._chunks)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> SearchResults:
        """検索.

        Args:
            query: 検索クエリ
            top_k: 上位k件
            filters: フィルタ（paper_id等）

        Returns:
            SearchResults
        """
        import time

        start = time.time()

        if not self._loaded or not self._chunks:
            return SearchResults(query=query)

        # BM25検索
        raw_results = self.bm25.search(query, top_k=top_k * 2)  # フィルタ用に多めに取得

        results = []
        query_lower = query.lower()

        for doc_idx, score in raw_results:
            if len(results) >= top_k:
                break

            chunk = self._chunks[doc_idx]

            # フィルタ適用
            if filters:
                if "paper_id" in filters and chunk.get("paper_id") != filters["paper_id"]:
                    continue

            # ハイライト
            highlights = self._extract_highlights(chunk.get("text", ""), query_lower)

            results.append(
                SearchResult(
                    chunk_id=chunk.get("chunk_id", ""),
                    paper_id=chunk.get("paper_id", ""),
                    paper_title=chunk.get("paper_title", ""),
                    text=chunk.get("text", ""),
                    score=score,
                    locator={
                        "section": chunk.get("section", ""),
                        "paragraph": chunk.get("paragraph_index", 0),
                        "char_start": chunk.get("char_start", 0),
                        "char_end": chunk.get("char_end", 0),
                    },
                    highlights=highlights,
                )
            )

        elapsed = (time.time() - start) * 1000

        return SearchResults(
            results=results,
            total=len(results),
            query=query,
            took_ms=elapsed,
        )

    def _extract_highlights(self, text: str, query: str) -> list[str]:
        """クエリに関連する文をハイライト抽出."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        query_words = set(re.findall(r"\b[a-z]+\b", query.lower()))

        highlights = []
        for sent in sentences:
            sent_lower = sent.lower()
            if any(w in sent_lower for w in query_words):
                highlights.append(sent.strip())
                if len(highlights) >= 3:
                    break

        return highlights


# グローバルエンジンインスタンス
_engine: SearchEngine | None = None


def get_search_engine() -> SearchEngine:
    """グローバル検索エンジンを取得."""
    global _engine
    if _engine is None:
        _engine = SearchEngine()
    return _engine


def search(query: str, top_k: int = 10) -> SearchResults:
    """便利関数: 検索."""
    engine = get_search_engine()
    return engine.search(query, top_k)