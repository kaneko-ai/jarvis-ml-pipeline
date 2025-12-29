"""KB update hooks for retrieval index."""
from __future__ import annotations

from jarvis_core.retrieval.indexer import RetrievalIndexer


def update_retrieval_index_for_kb() -> None:
    """Update retrieval index after KB changes."""
    indexer = RetrievalIndexer()
    indexer.update()
