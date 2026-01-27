"""Hybrid Retriever (Phase 25).

Combines Vector and BM25 search results using Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

import numpy as np

from jarvis_core.embeddings.model import DeterministicEmbeddingModel
from jarvis_core.retrieval.bm25 import BM25Retriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Orchestrates Hybrid Retrieval (Vector + BM25)."""

    def __init__(self, embedding_model: DeterministicEmbeddingModel = None):
        self.embedding_model = embedding_model or DeterministicEmbeddingModel()
        self.bm25 = BM25Retriever()

        # Need a vector store access - for simplicity assuming in-memory or passed in search
        # In real prod, this interfaces with Chroma/FAISS
        self.corpus: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None

    def fit(self, corpus: List[Dict[str, Any]], text_key: str = "text"):
        """Index corpus for both BM25 and Vector search."""
        self.corpus = corpus

        # 1. Build BM25
        self.bm25.fit(corpus, text_key=text_key)

        # 2. Build Vectors (in-memory for simple hybrid)
        texts = [doc.get(text_key, "") for doc in corpus]
        self.vectors = self.embedding_model.embed(texts)
        logger.info(f"Hybrid index built: {len(corpus)} docs")

    def search(self, query: str, top_k: int = 10, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """Perform hybrid search.

        Args:
            query: Search query
            top_k: Number of results
            alpha: Weight for vector search (0.0=BM25 only, 1.0=Vector only)
                   However, for RRF we usually constant k.
                   Here we use simple linear score fusion if scores are normalized,
                   or RRF if ranks are used. Implementing RRF as it's more robust.
        """
        # 1. BM25 Search
        bm25_results = self.bm25.search(query, top_k=top_k * 2)

        # 2. Vector Search
        query_vec = self.embedding_model.embed(query)[0]
        if self.vectors is not None and len(self.vectors) > 0:
            # Cosine similarity
            sims = np.dot(self.vectors, query_vec)
            top_indices = np.argsort(sims)[::-1][: top_k * 2]

            vector_results = []
            for idx in top_indices:
                doc = self.corpus[idx].copy()
                doc["score"] = float(sims[idx])
                vector_results.append(doc)
        else:
            vector_results = []

        # 3. Reciprocal Rank Fusion
        return self._rrf_merge(bm25_results, vector_results, k=60, top_n=top_k)

    def _rrf_merge(
        self, list1: List[Dict], list2: List[Dict], k: int = 60, top_n: int = 10
    ) -> List[Dict]:
        """Merge two result lists using RRF."""
        scores = {}

        # Helper to process a list
        def process_list(results):
            for rank, item in enumerate(results):
                doc_id = item.get("chunk_id")
                if not doc_id:
                    continue

                if doc_id not in scores:
                    scores[doc_id] = {"doc": item, "score": 0.0}

                # RRF score = 1 / (k + rank)
                scores[doc_id]["score"] += 1.0 / (k + rank + 1)

        process_list(list1)
        process_list(list2)

        # Sort by RRF score
        sorted_docs = sorted(scores.values(), key=lambda x: x["score"], reverse=True)

        return [item["doc"] for item in sorted_docs[:top_n]]
