"""BM25 Sparse Embedding Module.

Provides BM25-based sparse retrieval with persistence.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.2.2
"""

from __future__ import annotations

import json
import logging
import pickle
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BM25Config:
    """BM25 algorithm configuration."""

    k1: float = 1.5  # Term saturation parameter
    b: float = 0.75  # Length normalization parameter


@dataclass
class BM25Index:
    """BM25 sparse embedding index with persistence.

    Implements the Okapi BM25 ranking function for keyword search.
    Supports building, searching, saving, and loading the index.

    Example:
        >>> index = BM25Index()
        >>> corpus = ["machine learning", "deep learning", "natural language"]
        >>> index.build(corpus, ids=["doc1", "doc2", "doc3"])
        >>> results = index.search("machine", top_k=2)
        >>> print(results)
        [('doc1', 0.85), ('doc2', 0.32)]
    """

    config: BM25Config = field(default_factory=BM25Config)
    _corpus: list[str] = field(default_factory=list)
    _tokenized_corpus: list[list[str]] = field(default_factory=list)
    _doc_ids: list[str] = field(default_factory=list)
    _bm25: object = field(default=None)
    _initialized: bool = field(default=False)

    def build(
        self,
        corpus: list[str],
        ids: list[str] | None = None,
    ) -> None:
        """Build the BM25 index from a corpus.

        Args:
            corpus: List of document texts
            ids: Optional list of document IDs (auto-generated if not provided)
        """
        if not corpus:
            logger.warning("Empty corpus provided to BM25Index.build()")
            return

        self._corpus = corpus
        self._doc_ids = ids if ids else [str(i) for i in range(len(corpus))]

        if len(self._doc_ids) != len(corpus):
            raise ValueError(
                f"IDs count ({len(self._doc_ids)}) must match corpus count ({len(corpus)})"
            )

        # Tokenize corpus
        self._tokenized_corpus = [self._tokenize(doc) for doc in corpus]

        # Build BM25 index
        try:
            from rank_bm25 import BM25Okapi

            self._bm25 = BM25Okapi(
                self._tokenized_corpus,
                k1=self.config.k1,
                b=self.config.b,
            )
            self._initialized = True
            logger.info(f"BM25Index built with {len(corpus)} documents")
        except ImportError:
            logger.warning("rank_bm25 not installed. " "Install with: pip install rank-bm25")
            self._bm25 = None

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization with lowercasing and punctuation removal."""
        import re

        # Lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()

        # Remove very short tokens
        tokens = [t for t in tokens if len(t) > 1]

        return tokens

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search the index with a query.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples sorted by score descending
        """
        if not self._initialized or self._bm25 is None:
            logger.warning("BM25Index not initialized. Call build() first.")
            return []

        if not query.strip():
            return []

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []

        scores = self._bm25.get_scores(tokenized_query)
        # logger.debug(f"BM25 Search: query={tokenized_query}, scores={scores}")
        # print(f"DEBUG: BM25 Search: query={tokenized_query}, scores={scores}")

        # Get top-k indices
        scored_indices = [(i, float(s)) for i, s in enumerate(scores)]
        scored_indices.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_indices[:top_k]:
            if score > 0:
                results.append((self._doc_ids[idx], score))

        return results

    def save(self, path: Path) -> None:
        """Save the index to disk.

        Args:
            path: Path to save the index
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save metadata as JSON
        metadata = {
            "config": {
                "k1": self.config.k1,
                "b": self.config.b,
            },
            "doc_ids": self._doc_ids,
            "doc_count": len(self._corpus),
        }

        metadata_path = path.with_suffix(".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Save the corpus and tokenized corpus as pickle
        # We don't save the BM25 object itself as it may not be picklable
        # Instead we rebuild it on load
        data = {
            "corpus": self._corpus,
            "tokenized_corpus": self._tokenized_corpus,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"BM25Index saved to {path}")

    @classmethod
    def load(cls, path: Path) -> BM25Index:
        """Load an index from disk.

        Args:
            path: Path to load the index from

        Returns:
            Loaded BM25Index
        """
        path = Path(path)

        # Load metadata
        metadata_path = path.with_suffix(".json")
        if metadata_path.exists():
            with open(metadata_path, encoding="utf-8") as f:
                metadata = json.load(f)
            config = BM25Config(**metadata.get("config", {}))
            doc_ids = metadata.get("doc_ids", [])
        else:
            config = BM25Config()
            doc_ids = []

        # Load the BM25 object and corpus
        with open(path, "rb") as f:
            data = pickle.load(f)

        index = cls(config=config)
        index._corpus = data.get("corpus", [])
        index._tokenized_corpus = data.get("tokenized_corpus", [])
        index._doc_ids = doc_ids if doc_ids else [str(i) for i in range(len(index._corpus))]

        # Rebuild BM25 index from tokenized corpus
        if index._tokenized_corpus:
            try:
                from rank_bm25 import BM25Okapi

                index._bm25 = BM25Okapi(
                    index._tokenized_corpus,
                    k1=index.config.k1,
                    b=index.config.b,
                )
                index._initialized = True
            except ImportError:
                logger.warning("rank_bm25 not installed. Cannot initialize index.")
                index._bm25 = None
                index._initialized = False

        logger.info(f"BM25Index loaded from {path}")
        return index

    def add_document(self, doc_id: str, text: str) -> None:
        """Add a single document to the index (rebuilds index).

        For bulk additions, use build() instead.

        Args:
            doc_id: Document ID
            text: Document text
        """
        if doc_id in self._doc_ids:
            # Update existing document
            idx = self._doc_ids.index(doc_id)
            self._corpus[idx] = text
        else:
            self._corpus.append(text)
            self._doc_ids.append(doc_id)

        # Rebuild index
        self.build(self._corpus, self._doc_ids)

    @property
    def doc_count(self) -> int:
        """Get the number of documents in the index."""
        return len(self._corpus)

    def get_document(self, doc_id: str) -> str | None:
        """Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document text or None if not found
        """
        try:
            idx = self._doc_ids.index(doc_id)
            return self._corpus[idx]
        except ValueError:
            return None