"""Hybrid Search Module.

Combines dense (vector) and sparse (BM25) retrieval with fusion.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.2.3
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import numpy as np

from jarvis_core.embeddings.bm25 import BM25Index
from jarvis_core.embeddings.sentence_transformer import (
    SentenceTransformerEmbedding,
)

logger = logging.getLogger(__name__)


class FusionMethod(Enum):
    """Methods for combining sparse and dense search results."""

    RRF = "rrf"  # Reciprocal Rank Fusion
    LINEAR = "linear"  # Linear combination of normalized scores


@dataclass
class SearchResult:
    """A single search result."""

    doc_id: str
    text: str
    score: float
    dense_score: float = 0.0
    sparse_score: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class HybridSearchResult:
    """Results from a hybrid search."""

    results: list[SearchResult]
    took_ms: int = 0
    total_candidates: int = 0
    fusion_method: str = "rrf"


class HybridSearch:
    """Hybrid search combining dense (vector) and sparse (BM25) retrieval.

    Supports multiple fusion methods:
    - RRF (Reciprocal Rank Fusion): Combines rankings, robust to score scales
    - Linear: Weighted combination of normalized scores

    Example:
        >>> hybrid = HybridSearch()
        >>> corpus = ["machine learning", "deep learning", "NLP"]
        >>> hybrid.index(corpus, ids=["d1", "d2", "d3"])
        >>> results = hybrid.search("machine", top_k=2)
        >>> print(results.results[0].doc_id)
        'd1'
    """

    def __init__(
        self,
        dense_model: SentenceTransformerEmbedding | None = None,
        sparse_index: BM25Index | None = None,
        fusion_method: FusionMethod = FusionMethod.RRF,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        rrf_k: int = 60,
    ):
        """Initialize the hybrid search engine.

        Args:
            dense_model: Dense embedding model (default: MiniLM)
            sparse_index: BM25 sparse index
            fusion_method: Method for combining results
            dense_weight: Weight for dense scores (linear fusion)
            sparse_weight: Weight for sparse scores (linear fusion)
            rrf_k: RRF constant (higher = more weight to lower ranks)
        """
        self._dense_model = dense_model
        self._sparse_index = sparse_index or BM25Index()
        self._fusion_method = fusion_method
        self._dense_weight = dense_weight
        self._sparse_weight = sparse_weight
        self._rrf_k = rrf_k

        # Document storage
        self._corpus: list[str] = []
        self._doc_ids: list[str] = []
        self._metadata: dict[str, dict] = {}

        # Dense index (vectors)
        self._vectors: np.ndarray | None = None

    def _get_dense_model(self) -> SentenceTransformerEmbedding:
        """Lazy initialization of dense model."""
        if self._dense_model is None:
            self._dense_model = SentenceTransformerEmbedding.for_general()
        return self._dense_model

    def index(
        self,
        corpus: list[str],
        ids: list[str] | None = None,
        metadata: list[dict] | None = None,
    ) -> None:
        """Index a corpus for hybrid search.

        Args:
            corpus: List of document texts
            ids: Optional list of document IDs
            metadata: Optional list of metadata dicts per document
        """
        if not corpus:
            logger.warning("Empty corpus provided to HybridSearch.index()")
            return

        self._corpus = corpus
        self._doc_ids = ids if ids else [str(i) for i in range(len(corpus))]

        if len(self._doc_ids) != len(corpus):
            raise ValueError(
                f"IDs count ({len(self._doc_ids)}) must match corpus count ({len(corpus)})"
            )

        # Store metadata
        if metadata:
            for doc_id, meta in zip(self._doc_ids, metadata):
                self._metadata[doc_id] = meta

        # Build sparse index
        logger.info(f"Building BM25 index for {len(corpus)} documents...")
        self._sparse_index.build(corpus, self._doc_ids)

        # Build dense index
        logger.info(f"Computing dense embeddings for {len(corpus)} documents...")
        model = self._get_dense_model()
        self._vectors = model.encode(corpus)

        logger.info(f"Hybrid index built: {len(corpus)} documents")

    def search(
        self,
        query: str,
        top_k: int = 10,
        mode: str = "hybrid",
    ) -> HybridSearchResult:
        """Search the index.

        Args:
            query: Search query
            top_k: Number of results to return
            mode: Search mode ("hybrid", "dense", "sparse")

        Returns:
            HybridSearchResult with ranked results
        """
        import time

        start_time = time.time()

        if not self._corpus:
            return HybridSearchResult(results=[], took_ms=0, total_candidates=0)

        # Get sparse results
        sparse_results: dict[str, float] = {}
        if mode in ("hybrid", "sparse"):
            for doc_id, score in self._sparse_index.search(query, top_k=top_k * 3):
                sparse_results[doc_id] = score

        # Get dense results
        dense_results: dict[str, float] = {}
        if mode in ("hybrid", "dense") and self._vectors is not None:
            model = self._get_dense_model()
            query_vec = model.encode(query)

            # Cosine similarity (vectors are normalized)
            similarities = np.dot(self._vectors, query_vec.T).flatten()

            # Get top candidates
            top_indices = np.argsort(similarities)[::-1][: top_k * 3]
            for idx in top_indices:
                doc_id = self._doc_ids[idx]
                dense_results[doc_id] = float(similarities[idx])

        # Combine results
        if mode == "sparse":
            combined = self._rank_by_score(sparse_results)
        elif mode == "dense":
            combined = self._rank_by_score(dense_results)
        else:
            if self._fusion_method == FusionMethod.RRF:
                combined = self._rrf_fusion(sparse_results, dense_results)
            else:
                combined = self._linear_fusion(sparse_results, dense_results)

        # Build results
        results = []
        for doc_id, score in combined[:top_k]:
            idx = self._doc_ids.index(doc_id)
            results.append(
                SearchResult(
                    doc_id=doc_id,
                    text=self._corpus[idx],
                    score=score,
                    dense_score=dense_results.get(doc_id, 0.0),
                    sparse_score=sparse_results.get(doc_id, 0.0),
                    metadata=self._metadata.get(doc_id, {}),
                )
            )

        took_ms = int((time.time() - start_time) * 1000)
        total_candidates = len(set(sparse_results) | set(dense_results))

        return HybridSearchResult(
            results=results,
            took_ms=took_ms,
            total_candidates=total_candidates,
            fusion_method=self._fusion_method.value if mode == "hybrid" else mode,
        )

    def _rank_by_score(self, scores: dict[str, float]) -> list[tuple[str, float]]:
        """Sort by score descending."""
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def _rrf_fusion(
        self,
        sparse_scores: dict[str, float],
        dense_scores: dict[str, float],
    ) -> list[tuple[str, float]]:
        """Reciprocal Rank Fusion.

        RRF score = sum(1 / (k + rank)) for each ranking
        """
        # Create rankings
        sparse_rank = {
            doc_id: rank + 1
            for rank, (doc_id, _) in enumerate(
                sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)
            )
        }
        dense_rank = {
            doc_id: rank + 1
            for rank, (doc_id, _) in enumerate(
                sorted(dense_scores.items(), key=lambda x: x[1], reverse=True)
            )
        }

        # Compute RRF scores
        all_docs = set(sparse_scores) | set(dense_scores)
        rrf_scores = {}

        for doc_id in all_docs:
            score = 0.0
            if doc_id in sparse_rank:
                score += 1.0 / (self._rrf_k + sparse_rank[doc_id])
            if doc_id in dense_rank:
                score += 1.0 / (self._rrf_k + dense_rank[doc_id])
            rrf_scores[doc_id] = score

        return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    def _linear_fusion(
        self,
        sparse_scores: dict[str, float],
        dense_scores: dict[str, float],
    ) -> list[tuple[str, float]]:
        """Linear combination of normalized scores."""
        # Normalize scores to [0, 1]
        sparse_norm = self._normalize_scores(sparse_scores)
        dense_norm = self._normalize_scores(dense_scores)

        # Combine
        all_docs = set(sparse_scores) | set(dense_scores)
        combined = {}

        for doc_id in all_docs:
            s_score = sparse_norm.get(doc_id, 0.0) * self._sparse_weight
            d_score = dense_norm.get(doc_id, 0.0) * self._dense_weight
            combined[doc_id] = s_score + d_score

        return sorted(combined.items(), key=lambda x: x[1], reverse=True)

    def _normalize_scores(self, scores: dict[str, float]) -> dict[str, float]:
        """Min-max normalization of scores."""
        if not scores:
            return {}

        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            return dict.fromkeys(scores, 1.0)

        return {k: (v - min_val) / (max_val - min_val) for k, v in scores.items()}

    def save(self, path: Path) -> None:
        """Save the hybrid index to disk.

        Args:
            path: Directory to save the index
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save sparse index
        self._sparse_index.save(path / "bm25.pkl")

        # Save dense vectors
        if self._vectors is not None:
            np.save(path / "vectors.npy", self._vectors)

        # Save corpus and metadata
        import json

        with open(path / "corpus.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "corpus": self._corpus,
                    "doc_ids": self._doc_ids,
                    "metadata": self._metadata,
                    "config": {
                        "fusion_method": self._fusion_method.value,
                        "dense_weight": self._dense_weight,
                        "sparse_weight": self._sparse_weight,
                        "rrf_k": self._rrf_k,
                    },
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(f"HybridSearch index saved to {path}")

    @classmethod
    def load(
        cls, path: Path, dense_model: SentenceTransformerEmbedding | None = None
    ) -> HybridSearch:
        """Load a hybrid index from disk.

        Args:
            path: Directory containing the saved index
            dense_model: Optional dense model (for computing new query embeddings)

        Returns:
            Loaded HybridSearch instance
        """
        path = Path(path)

        # Load corpus and config
        import json

        with open(path / "corpus.json", encoding="utf-8") as f:
            data = json.load(f)

        config = data.get("config", {})

        # Create instance
        hybrid = cls(
            dense_model=dense_model,
            fusion_method=FusionMethod(config.get("fusion_method", "rrf")),
            dense_weight=config.get("dense_weight", 0.6),
            sparse_weight=config.get("sparse_weight", 0.4),
            rrf_k=config.get("rrf_k", 60),
        )

        hybrid._corpus = data.get("corpus", [])
        hybrid._doc_ids = data.get("doc_ids", [])
        hybrid._metadata = data.get("metadata", {})

        # Load sparse index
        hybrid._sparse_index = BM25Index.load(path / "bm25.pkl")

        # Load dense vectors
        vectors_path = path / "vectors.npy"
        if vectors_path.exists():
            hybrid._vectors = np.load(vectors_path)

        logger.info(f"HybridSearch index loaded from {path}")
        return hybrid

    @property
    def doc_count(self) -> int:
        """Get the number of indexed documents."""
        return len(self._corpus)