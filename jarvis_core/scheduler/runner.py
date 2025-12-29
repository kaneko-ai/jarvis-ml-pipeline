"""Scheduler hook for retrieval index updates after runs."""
from __future__ import annotations

from jarvis_core.retrieval.indexer import RetrievalIndexer


def update_retrieval_index_after_run(run_id: str) -> None:
    """Incrementally update retrieval index after a run completes."""
    indexer = RetrievalIndexer()
    indexer.update()
