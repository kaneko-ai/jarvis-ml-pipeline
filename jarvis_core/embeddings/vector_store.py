"""Vector Store Abstraction (Phase 37).

Defines the abstract base class for vector stores and provides the FAISS implementation.
"""

from __future__ import annotations

import abc
import json
import logging
from pathlib import Path
from typing import Any, List, Tuple, Dict

import numpy as np

logger = logging.getLogger(__name__)


class VectorStore(abc.ABC):
    """Abstract base class for vector stores."""

    @abc.abstractmethod
    def add(
        self,
        embeddings: np.ndarray | List[List[float]],
        doc_ids: List[str],
        metadata: List[Dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to the store."""
        pass

    @abc.abstractmethod
    def search(
        self,
        query_embedding: np.ndarray | List[float],
        top_k: int = 10,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar documents.

        Returns:
            List of (doc_id, score, metadata) tuples.
        """
        pass

    @abc.abstractmethod
    def save(self, path: Path) -> None:
        """Persist the store to disk."""
        pass

    @classmethod
    @abc.abstractmethod
    def load(cls, path: Path) -> VectorStore:
        """Load the store from disk."""
        pass

    @property
    @abc.abstractmethod
    def count(self) -> int:
        """Return the number of documents in the store."""
        pass


class FAISSVectorStore(VectorStore):
    """FAISS-based vector store implementation."""

    def __init__(self, dimension: int, index_type: str = "flat"):
        self._dimension = dimension
        self._index = None
        self._doc_ids: List[str] = []
        self._metadata: List[Dict[str, Any]] = []
        self._index_type = index_type
        self._faiss = None

    def _load_faiss(self):
        if self._faiss is None:
            try:
                import faiss

                self._faiss = faiss
            except ImportError:
                raise ImportError("faiss is required. Install with: pip install faiss-cpu")
        return self._faiss

    def build(
        self,
        embeddings: np.ndarray,
        doc_ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Build the clean index."""
        faiss = self._load_faiss()

        if self._index_type == "flat":
            self._index = faiss.IndexFlatIP(self._dimension)
        elif self._index_type == "ivf":
            nlist = min(100, len(doc_ids) // 10 + 1)
            quantizer = faiss.IndexFlatIP(self._dimension)
            self._index = faiss.IndexIVFFlat(quantizer, self._dimension, nlist)
            embeddings_f32 = embeddings.astype(np.float32)
            self._index.train(embeddings_f32)
        else:
            raise ValueError(f"Unknown index type: {self._index_type}")

        normalized = self._normalize(embeddings)
        self._index.add(normalized.astype(np.float32))

        self._doc_ids = doc_ids
        self._metadata = metadata or [{} for _ in doc_ids]
        logger.info(f"Built FAISS index with {len(doc_ids)} documents")

    def add(
        self,
        embeddings: np.ndarray | List[List[float]],
        doc_ids: List[str],
        metadata: List[Dict[str, Any]] | None = None,
    ) -> None:
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        if self._index is None:
            self.build(embeddings, doc_ids, metadata)
            return

        normalized = self._normalize(embeddings)
        self._index.add(normalized.astype(np.float32))
        self._doc_ids.extend(doc_ids)
        self._metadata.extend(metadata or [{} for _ in doc_ids])

    def search(
        self,
        query_embedding: np.ndarray | List[float],
        top_k: int = 10,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if self._index is None:
            raise ValueError("Index not built")

        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)

        query_norm = self._normalize(query_embedding.reshape(1, -1))
        distances, indices = self._index.search(query_norm.astype(np.float32), top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self._doc_ids):
                results.append(
                    (
                        self._doc_ids[idx],
                        float(distances[0][i]),
                        self._metadata[idx],
                    )
                )
        return results

    def save(self, path: Path) -> None:
        faiss = self._load_faiss()
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path / "faiss.index"))
        with open(path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "doc_ids": self._doc_ids,
                    "metadata": self._metadata,
                    "dimension": self._dimension,
                    "index_type": self._index_type,
                },
                f,
            )
        logger.info(f"Saved FAISS index to {path}")

    @classmethod
    def load(cls, path: Path) -> FAISSVectorStore:
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss is required.")

        path = Path(path)
        with open(path / "metadata.json", encoding="utf-8") as f:
            meta = json.load(f)

        store = cls(dimension=meta["dimension"], index_type=meta["index_type"])
        store._index = faiss.read_index(str(path / "faiss.index"))
        store._doc_ids = meta["doc_ids"]
        store._metadata = meta["metadata"]
        return store

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=-1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    @property
    def count(self) -> int:
        return len(self._doc_ids)