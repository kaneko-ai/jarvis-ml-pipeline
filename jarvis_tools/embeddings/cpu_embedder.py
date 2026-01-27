"""CPU Embedder.

Per RP-118, provides CPU-friendly embeddings with caching.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmbeddingResult:
    """Result of embedding computation."""

    embedding: List[float]
    model: str
    cached: bool
    dim: int


class EmbeddingCache:
    """Disk cache for embeddings."""

    def __init__(self, cache_dir: str = "data/embeddings_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, text: str, model: str) -> str:
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding."""
        key = self._cache_key(text, model)
        path = self._cache_path(key)

        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                return data.get("embedding")
        return None

    def put(self, text: str, model: str, embedding: List[float]) -> None:
        """Cache an embedding."""
        key = self._cache_key(text, model)
        path = self._cache_path(key)

        with open(path, "w") as f:
            json.dump({"embedding": embedding, "model": model}, f)


class CPUEmbedder:
    """CPU-friendly embedder with fallback to simple vectors."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: str = "data/embeddings_cache",
        use_cache: bool = True,
    ):
        self.model_name = model_name
        self.cache = EmbeddingCache(cache_dir) if use_cache else None
        self._model = None
        self._available = None

    def _load_model(self):
        """Lazy load the embedding model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._available = True
        except ImportError:
            self._available = False

    def is_available(self) -> bool:
        """Check if embedding model is available."""
        if self._available is None:
            self._load_model()
        return self._available

    def embed(self, text: str) -> EmbeddingResult:
        """Embed a single text.

        Falls back to simple TF-IDF-like vector if model unavailable.
        """
        # Check cache
        if self.cache:
            cached = self.cache.get(text, self.model_name)
            if cached:
                return EmbeddingResult(
                    embedding=cached,
                    model=self.model_name,
                    cached=True,
                    dim=len(cached),
                )

        # Try model
        if self.is_available():
            embedding = self._model.encode(text).tolist()
        else:
            # Fallback: simple hash-based pseudo-embedding
            embedding = self._fallback_embed(text)

        # Cache result
        if self.cache:
            self.cache.put(text, self.model_name, embedding)

        return EmbeddingResult(
            embedding=embedding,
            model=self.model_name if self.is_available() else "fallback_hash",
            cached=False,
            dim=len(embedding),
        )

    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Embed multiple texts."""
        return [self.embed(text) for text in texts]

    def _fallback_embed(self, text: str, dim: int = 64) -> List[float]:
        """Simple fallback embedding using hash."""
        # Create reproducible pseudo-embedding
        words = text.lower().split()
        embedding = [0.0] * dim

        for i, word in enumerate(words[:100]):
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for j in range(dim):
                embedding[j] += ((word_hash >> j) & 1) * 0.1

        # Normalize
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding


# Global embedder
_embedder: Optional[CPUEmbedder] = None


def get_embedder() -> CPUEmbedder:
    """Get global embedder."""
    global _embedder
    if _embedder is None:
        _embedder = CPUEmbedder()
    return _embedder


def embed_text(text: str) -> List[float]:
    """Embed text using global embedder."""
    return get_embedder().embed(text).embedding
