"""Hybrid Retrieval - BM25 + Dense Embedding Fusion.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.2: ローカル埋め込み
Implements Reciprocal Rank Fusion (RRF) for combining sparse and dense retrieval.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Single retrieval result."""

    doc_id: str
    text: str
    score: float
    source: str  # "bm25", "dense", or "hybrid"
    metadata: dict | None = None


class BM25Retriever:
    """BM25 sparse retriever using rank_bm25."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._index = None
        self._corpus = []
        self._doc_ids = []

    def index(self, documents: list[dict]) -> None:
        """Index documents for BM25 retrieval.

        Args:
            documents: List of dicts with 'id' and 'text' keys.
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.warning("rank_bm25 not installed, BM25 disabled")
            return

        self._corpus = []
        self._doc_ids = []

        for doc in documents:
            doc_id = doc.get("id", str(len(self._doc_ids)))
            text = doc.get("text", "")

            # Simple tokenization
            tokens = text.lower().split()
            self._corpus.append(tokens)
            self._doc_ids.append(doc_id)

        self._index = BM25Okapi(self._corpus, k1=self.k1, b=self.b)
        logger.info(f"BM25 index built with {len(self._corpus)} documents")

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search with BM25.

        Args:
            query: Query string.
            top_k: Number of results.

        Returns:
            List of (doc_id, score) tuples.
        """
        if self._index is None:
            return []

        tokens = query.lower().split()
        scores = self._index.get_scores(tokens)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self._doc_ids[idx], float(scores[idx])))

        return results


class DenseRetriever:
    """Dense retriever using sentence embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._embeddings = None
        self._doc_ids = []
        self._texts = []

    def _load_model(self) -> None:
        """Lazy load embedding model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed")
            self._model = None

    def index(self, documents: list[dict]) -> None:
        """Index documents with dense embeddings.

        Args:
            documents: List of dicts with 'id' and 'text' keys.
        """
        self._load_model()
        if self._model is None:
            return

        self._doc_ids = []
        self._texts = []

        for doc in documents:
            doc_id = doc.get("id", str(len(self._doc_ids)))
            text = doc.get("text", "")
            self._doc_ids.append(doc_id)
            self._texts.append(text)

        self._embeddings = self._model.encode(
            self._texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        logger.info(f"Dense index built with {len(self._texts)} documents")

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search with dense embeddings.

        Args:
            query: Query string.
            top_k: Number of results.

        Returns:
            List of (doc_id, score) tuples.
        """
        if self._model is None or self._embeddings is None:
            return []

        query_emb = self._model.encode([query], convert_to_numpy=True)[0]

        # Cosine similarity
        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_emb)
        norms[norms == 0] = 1  # Avoid division by zero
        scores = np.dot(self._embeddings, query_emb) / norms

        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append((self._doc_ids[idx], float(scores[idx])))

        return results


class HybridRetriever:
    """Hybrid retriever combining BM25 and dense embeddings.

    Uses Reciprocal Rank Fusion (RRF) for score combination.
    """

    def __init__(
        self,
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5,
        rrf_k: int = 60,
        dense_model: str = "all-MiniLM-L6-v2",
    ):
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.rrf_k = rrf_k

        self.bm25 = BM25Retriever()
        self.dense = DenseRetriever(model_name=dense_model)
        self._documents: dict[str, dict] = {}

    def index(self, documents: list[dict]) -> None:
        """Index documents for hybrid retrieval.

        Args:
            documents: List of dicts with 'id' and 'text' keys.
        """
        # Store documents for later retrieval
        for doc in documents:
            doc_id = doc.get("id", str(len(self._documents)))
            self._documents[doc_id] = doc

        # Index in both retrievers
        self.bm25.index(documents)
        self.dense.index(documents)

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_rrf: bool = True,
    ) -> list[RetrievalResult]:
        """Hybrid search combining BM25 and dense.

        Args:
            query: Query string.
            top_k: Number of results.
            use_rrf: Use Reciprocal Rank Fusion (True) or weighted sum (False).

        Returns:
            List of RetrievalResult objects.
        """
        # Get results from both retrievers
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        dense_results = self.dense.search(query, top_k=top_k * 2)

        if use_rrf:
            combined = self._rrf_fusion(bm25_results, dense_results)
        else:
            combined = self._weighted_fusion(bm25_results, dense_results)

        # Convert to RetrievalResult
        results = []
        for doc_id, score in combined[:top_k]:
            doc = self._documents.get(doc_id, {})
            results.append(
                RetrievalResult(
                    doc_id=doc_id,
                    text=doc.get("text", ""),
                    score=score,
                    source="hybrid",
                    metadata=doc.get("metadata"),
                )
            )

        return results

    def _rrf_fusion(
        self,
        bm25_results: list[tuple[str, float]],
        dense_results: list[tuple[str, float]],
    ) -> list[tuple[str, float]]:
        """Reciprocal Rank Fusion.

        RRF(d) = Σ 1 / (k + rank(d))
        """
        scores: dict[str, float] = {}

        # BM25 contribution
        for rank, (doc_id, _) in enumerate(bm25_results, 1):
            rrf_score = self.bm25_weight / (self.rrf_k + rank)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score

        # Dense contribution
        for rank, (doc_id, _) in enumerate(dense_results, 1):
            rrf_score = self.dense_weight / (self.rrf_k + rank)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score

        # Sort by combined score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results

    def _weighted_fusion(
        self,
        bm25_results: list[tuple[str, float]],
        dense_results: list[tuple[str, float]],
    ) -> list[tuple[str, float]]:
        """Weighted sum fusion with score normalization."""
        scores: dict[str, float] = {}

        # Normalize BM25 scores
        if bm25_results:
            max_bm25 = max(s for _, s in bm25_results)
            for doc_id, score in bm25_results:
                norm_score = score / max_bm25 if max_bm25 > 0 else 0
                scores[doc_id] = self.bm25_weight * norm_score

        # Normalize dense scores (already 0-1 for cosine)
        for doc_id, score in dense_results:
            # Dense scores can be negative for cosine, shift to 0-1
            norm_score = (score + 1) / 2
            scores[doc_id] = scores.get(doc_id, 0) + self.dense_weight * norm_score

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results


# Convenience function
def create_hybrid_retriever(
    documents: list[dict],
    dense_model: str = "all-MiniLM-L6-v2",
) -> HybridRetriever:
    """Create and index a hybrid retriever.

    Args:
        documents: List of document dicts with 'id' and 'text'.
        dense_model: SentenceTransformers model name.

    Returns:
        Indexed HybridRetriever instance.
    """
    retriever = HybridRetriever(dense_model=dense_model)
    retriever.index(documents)
    return retriever