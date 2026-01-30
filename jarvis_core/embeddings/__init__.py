"""JARVIS Embeddings Module.

Consolidated embedding functionality for the JARVIS Research OS.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.2: ローカル埋め込み
"""

from jarvis_core.embeddings.bm25 import BM25Index
from jarvis_core.embeddings.hybrid import FusionMethod, HybridSearch
from jarvis_core.embeddings.sentence_transformer import (
    SentenceTransformerEmbedding,
    get_default_embedding_model,
)
from jarvis_core.embeddings.specter2 import SPECTER2Embedding


def get_embedding_model(model_type: str = "general"):
    """Get embedding model by type.

    Args:
        model_type: "general" or "scientific"

    Returns:
        Embedding model instance
    """
    if model_type == "scientific":
        return SPECTER2Embedding()
    return SentenceTransformerEmbedding()


__all__ = [
    "SentenceTransformerEmbedding",
    "get_default_embedding_model",
    "get_embedding_model",
    "BM25Index",
    "HybridSearch",
    "FusionMethod",
    "SPECTER2Embedding",
]