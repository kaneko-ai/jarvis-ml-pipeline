"""FAISS Vector Store.

High-performance vector similarity search using FAISS.
Per JARVIS_COMPLETION_INSTRUCTION Task 1.2.3
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for efficient similarity search."""

    def __init__(self, dimension: int, index_type: str = "flat"):
        """Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension
            index_type: Index type ("flat" for exact, "ivf" for approximate)
        """
        self._dimension = dimension
        self._index = None
        self._doc_ids: list[str] = []
        self._metadata: list[dict[str, Any]] = []
        self._index_type = index_type
        self._faiss = None

    def _load_faiss(self):
        """Lazy load FAISS."""
        if self._faiss is None:
            try:
                import faiss
                self._faiss = faiss
            except ImportError:
                raise ImportError(
                    "faiss is required. Install with: pip install faiss-cpu"
                )
        return self._faiss

    def build(
        self,
        embeddings: np.ndarray,
        doc_ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Build the FAISS index.
        
        Args:
            embeddings: Numpy array of shape (n_docs, dimension)
            doc_ids: List of document IDs
            metadata: Optional metadata for each document
        """
        faiss = self._load_faiss()

        if self._index_type == "flat":
            self._index = faiss.IndexFlatIP(self._dimension)
        elif self._index_type == "ivf":
            nlist = min(100, len(doc_ids) // 10 + 1)
            quantizer = faiss.IndexFlatIP(self._dimension)
            self._index = faiss.IndexIVFFlat(quantizer, self._dimension, nlist)
            # Train IVF index
            embeddings_f32 = embeddings.astype(np.float32)
            self._index.train(embeddings_f32)
        else:
            raise ValueError(f"Unknown index type: {self._index_type}")

        # Normalize and add
        normalized = self._normalize(embeddings)
        self._index.add(normalized.astype(np.float32))

        self._doc_ids = doc_ids
        self._metadata = metadata or [{} for _ in doc_ids]

        logger.info(f"Built FAISS index with {len(doc_ids)} documents")

    def add(
        self,
        embeddings: np.ndarray,
        doc_ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to existing index.
        
        Args:
            embeddings: Embeddings to add
            doc_ids: Document IDs
            metadata: Optional metadata
        """
        if self._index is None:
            self.build(embeddings, doc_ids, metadata)
            return

        normalized = self._normalize(embeddings)
        self._index.add(normalized.astype(np.float32))

        self._doc_ids.extend(doc_ids)
        self._metadata.extend(metadata or [{} for _ in doc_ids])

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            
        Returns:
            List of (doc_id, score, metadata) tuples
        """
        if self._index is None:
            raise ValueError("Index not built")

        query_norm = self._normalize(query_embedding.reshape(1, -1))
        distances, indices = self._index.search(query_norm.astype(np.float32), top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self._doc_ids):
                results.append((
                    self._doc_ids[idx],
                    float(distances[0][i]),
                    self._metadata[idx],
                ))

        return results

    def save(self, path: Path) -> None:
        """Save index to disk.
        
        Args:
            path: Directory to save to
        """
        faiss = self._load_faiss()
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self._index, str(path / "faiss.index"))

        # Save metadata
        with open(path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump({
                "doc_ids": self._doc_ids,
                "metadata": self._metadata,
                "dimension": self._dimension,
                "index_type": self._index_type,
            }, f)

        logger.info(f"Saved FAISS index to {path}")

    @classmethod
    def load(cls, path: Path) -> FAISSVectorStore:
        """Load index from disk.
        
        Args:
            path: Directory containing saved index
            
        Returns:
            Loaded FAISSVectorStore instance
        """
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss is required. Install with: pip install faiss-cpu")

        path = Path(path)

        with open(path / "metadata.json", encoding="utf-8") as f:
            meta = json.load(f)

        store = cls(dimension=meta["dimension"], index_type=meta["index_type"])
        store._index = faiss.read_index(str(path / "faiss.index"))
        store._doc_ids = meta["doc_ids"]
        store._metadata = meta["metadata"]

        logger.info(f"Loaded FAISS index from {path}")
        return store

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalize embeddings."""
        norms = np.linalg.norm(embeddings, axis=-1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    @property
    def count(self) -> int:
        """Return number of indexed documents."""
        return len(self._doc_ids)
