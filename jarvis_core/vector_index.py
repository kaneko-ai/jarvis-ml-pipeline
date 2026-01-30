"""Vector index for semantic retrieval.

This module provides:
- VectorRetriever: Build and search vector index
- DummyEmbedder: Hash-based embeddings for testing

Per RP23, this enables semantic search alongside BM25.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sources import ChunkResult


def dummy_embed(text: str, dim: int = 64) -> list[float]:
    """Create a deterministic embedding from text hash.

    This is for testing purposes only. In production,
    use actual embedding models.

    Args:
        text: Text to embed.
        dim: Embedding dimension.

    Returns:
        List of floats representing the embedding.
    """
    # Hash the text
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()

    # Convert hash to floats
    vector = []
    for i in range(dim):
        # Use pairs of hex chars to generate floats
        idx = (i * 2) % len(h)
        val = int(h[idx : idx + 2], 16) / 255.0
        # Normalize to [-1, 1]
        val = val * 2 - 1
        vector.append(val)

    # Normalize to unit vector
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]

    return vector


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


@dataclass
class IndexedChunk:
    """A chunk with its vector embedding."""

    chunk_id: str
    locator: str
    text: str
    preview: str
    vector: list[float]


class VectorRetriever:
    """Vector-based retriever using embeddings.

    Supports custom embedding functions. Default uses
    a deterministic hash-based embedding for testing.
    """

    def __init__(
        self,
        embed_fn: Callable[[str], list[float]] | None = None,
        dim: int = 64,
    ):
        """Initialize the retriever.

        Args:
            embed_fn: Function to embed text. Defaults to dummy_embed.
            dim: Embedding dimension (for dummy embedder).
        """
        self.embed_fn = embed_fn or (lambda text: dummy_embed(text, dim))
        self.dim = dim
        self.index: list[IndexedChunk] = []

    def build(self, chunks: list[ChunkResult]) -> None:
        """Build the index from chunks.

        Args:
            chunks: List of ChunkResult objects to index.
        """
        self.index = []
        for chunk in chunks:
            text = chunk.preview or ""
            vector = self.embed_fn(text)
            self.index.append(
                IndexedChunk(
                    chunk_id=chunk.chunk_id,
                    locator=chunk.locator,
                    text=text,
                    preview=chunk.preview,
                    vector=vector,
                )
            )

    def search(self, query: str, k: int = 5) -> list[ChunkResult]:
        """Search for similar chunks.

        Args:
            query: Query text.
            k: Number of results to return.

        Returns:
            List of ChunkResult objects sorted by similarity.
        """
        from .sources import ChunkResult

        if not self.index:
            return []

        query_vector = self.embed_fn(query)

        # Compute similarities
        scored = []
        for chunk in self.index:
            sim = cosine_similarity(query_vector, chunk.vector)
            scored.append((sim, chunk))

        # Sort by similarity (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top k
        results = []
        for sim, chunk in scored[:k]:
            results.append(
                ChunkResult(
                    chunk_id=chunk.chunk_id,
                    locator=chunk.locator,
                    preview=chunk.preview,
                )
            )

        return results


def get_relevant_chunks_vector(
    chunks: list[ChunkResult],
    query: str,
    k: int = 5,
    embed_fn: Callable[[str], list[float]] | None = None,
) -> list[ChunkResult]:
    """Convenience function for vector-based retrieval.

    Args:
        chunks: List of chunks to search.
        query: Query text.
        k: Number of results to return.
        embed_fn: Optional custom embedding function.

    Returns:
        List of most relevant ChunkResult objects.
    """
    retriever = VectorRetriever(embed_fn=embed_fn)
    retriever.build(chunks)
    return retriever.search(query, k=k)