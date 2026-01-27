"""KG package - Lightweight Knowledge Graph for CPU environments."""

from .store import KGStore, Triple
from .extract import extract_triples
from .retrieve import retrieve_2hop, KnowledgeGraph, Subgraph

__all__ = [
    "KGStore",
    "Triple",
    "extract_triples",
    "retrieve_2hop",
    "KnowledgeGraph",
    "Subgraph",
]
