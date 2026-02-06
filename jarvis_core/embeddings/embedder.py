"""Embedding helper module and compatibility layer."""

from __future__ import annotations

from jarvis_core.embeddings.sentence_transformer import SentenceTransformerEmbedding
from jarvis_core.embeddings.specter2 import SPECTER2Embedding


class DefaultEmbedder(SentenceTransformerEmbedding):
    """Alias for the default sentence-transformer embedder."""


def get_embedder(model_type: str = "general") -> SentenceTransformerEmbedding:
    """Get an embedder for a model type.

    Args:
        model_type: "general", "scientific", or "multilingual".

    Returns:
        Embedding model instance.
    """
    if model_type == "scientific":
        return SentenceTransformerEmbedding.for_scientific()
    if model_type == "multilingual":
        return SentenceTransformerEmbedding.for_multilingual()
    return SentenceTransformerEmbedding.for_general()


__all__ = [
    "DefaultEmbedder",
    "SentenceTransformerEmbedding",
    "SPECTER2Embedding",
    "get_embedder",
]
