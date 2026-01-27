"""Embeddings package."""

from .cpu_embedder import (
    CPUEmbedder,
    EmbeddingResult,
    get_embedder,
    embed_text,
)

__all__ = [
    "CPUEmbedder",
    "EmbeddingResult",
    "get_embedder",
    "embed_text",
]
