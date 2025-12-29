"""Embedding provider abstraction for retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np


@dataclass
class EmbeddingResult:
    vectors: np.ndarray
    model: str


class EmbeddingProvider:
    model_name: str = "unknown"

    def embed(self, texts: Iterable[str]) -> EmbeddingResult:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic hashing-based embeddings (no external dependency)."""

    def __init__(self, dim: int = 384, model_name: str = "hash-embedding-v1"):
        self.dim = dim
        self.model_name = model_name

    def _hash_to_vec(self, text: str) -> np.ndarray:
        import hashlib

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        numbers = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
        repeats = int(np.ceil(self.dim / len(numbers)))
        tiled = np.tile(numbers, repeats)[: self.dim]
        vec = tiled / 255.0
        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec
        return vec / norm

    def embed(self, texts: Iterable[str]) -> EmbeddingResult:
        vectors: List[np.ndarray] = []
        for text in texts:
            vectors.append(self._hash_to_vec(text))
        return EmbeddingResult(vectors=np.vstack(vectors), model=self.model_name)
