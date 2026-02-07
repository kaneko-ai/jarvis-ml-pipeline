"""BM25 Retriever (Phase 25).

Provides keyword-based sparse retrieval using rank-bm25.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Union

import numpy as np

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

logger = logging.getLogger(__name__)


class BM25Retriever:
    """Wrapper for BM25 keyword search."""

    def __init__(self, tokenizer=None):
        if BM25Okapi is None:
            raise ImportError("rank-bm25 not installed. Run `pip install rank-bm25`.")

        self.tokenizer = tokenizer or self._simple_tokenizer
        self.bm25 = None
        self.corpus: List[Dict[str, Any]] = []
        self._doc_ids: List[str] = []

    def _simple_tokenizer(self, text: str) -> List[str]:
        """Simple whitespace tokenizer with lowercase."""
        return text.lower().split()

    def fit(self, corpus: List[Dict[str, Any]], text_key: str = "text", id_key: str = "chunk_id"):
        """Index a corpus of documents."""
        self.corpus = corpus
        self._doc_ids = [doc.get(id_key, str(i)) for i, doc in enumerate(corpus)]

        tokenized_corpus = [self.tokenizer(doc.get(text_key, "")) for doc in corpus]

        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 index built with {len(corpus)} documents")

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search the index."""
        if not self.bm25:
            logger.warning("BM25 index not built. Call fit() first.")
            return []

        tokenized_query = self.tokenizer(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = scores[idx]
            if score <= 0:
                continue  # Filter zero matches

            doc = self.corpus[idx].copy()
            doc["score"] = float(score)
            results.append(doc)

        return results

    def save(self, path: Union[str, Path]):
        """Save index to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "corpus": self.corpus, "doc_ids": self._doc_ids}, f)

    def load(self, path: Union[str, Path]):
        """Load index from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)  # nosec B301: local cache file controlled by the service
            self.bm25 = data["bm25"]
            self.corpus = data["corpus"]
            self._doc_ids = data["doc_ids"]
