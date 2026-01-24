"""Unified Source Adapter (Phase 29).

Abstract base class for all data source connectors (e.g., PubMed, ArXiv, Web).
"""

from __future__ import annotations

import abc
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Standardized search result from any source."""
    source_id: str  # Original ID in the source (PMID, DOI, etc)
    title: str
    url: str
    abstract: str
    year: int
    authors: List[str]
    metadata: Dict[str, Any]

class SourceAdapter(abc.ABC):
    """Abstract base class for source adapters."""

    @property
    @abc.abstractmethod
    def source_name(self) -> str:
        """Name of the source (e.g., 'pubmed', 'arxiv')."""
        pass

    @abc.abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search the source for relevant papers."""
        pass

    @abc.abstractmethod
    def fetch_details(self, source_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch full details or full text for specific IDs."""
        pass

    def validate_query(self, query: str) -> bool:
        """Optional validation of query format."""
        return len(query.strip()) > 0
