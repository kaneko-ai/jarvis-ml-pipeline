"""JARVIS Embeddings Module.

Consolidated embedding functionality for the JARVIS Research OS.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.2: ローカル埋め込み
"""

from jarvis_core.embeddings.sentence_transformer import (
    SentenceTransformerEmbedding,
    get_default_embedding_model,
)
from jarvis_core.embeddings.bm25 import BM25Index
from jarvis_core.embeddings.hybrid import HybridSearch, FusionMethod

__all__ = [
    "SentenceTransformerEmbedding",
    "get_default_embedding_model",
    "BM25Index",
    "HybridSearch",
    "FusionMethod",
]
