"""
JARVIS arXiv API Client

実API接続: arXiv API
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any

import requests  # type: ignore[import-untyped]  # noqa: F401

from jarvis_core.sources.arxiv_client import ArxivClient as CoreArxivClient
from jarvis_core.sources.arxiv_client import ArxivPaper as CoreArxivPaper

logger = logging.getLogger(__name__)


@dataclass
class ArxivPaper:
    """arXiv論文 (Legacy Wrapper)."""

    arxiv_id: str
    title: str
    authors: list[str]
    year: int
    abstract: str
    categories: list[str]
    pdf_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": f"arXiv:{self.arxiv_id}",
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "source": "arxiv",
            "url": f"https://arxiv.org/abs/{self.arxiv_id}",
            "pdf_url": self.pdf_url,
            "categories": self.categories,
        }

    @classmethod
    def from_core(cls, paper: CoreArxivPaper) -> ArxivPaper:
        """Convert from core paper model."""
        year = paper.published.year if paper.published else 2024
        # Clean the ID (strip version suffix if needed for consistency)
        clean_id = paper.arxiv_id.split("v")[0] if "v" in paper.arxiv_id else paper.arxiv_id

        return cls(
            arxiv_id=clean_id,
            title=paper.title,
            authors=paper.authors[:5],
            year=year,
            abstract=paper.abstract,
            categories=paper.categories,
            pdf_url=paper.pdf_url,
        )


class ArxivClient:
    """arXiv API Client (Legacy Wrapper).

    Now uses jarvis_core.sources.arxiv_client as the engine.
    """

    def __init__(self, rate_limit: float = 3.0):
        self._core_client = CoreArxivClient(rate_limit_delay=rate_limit)

    def search(
        self,
        query: str,
        max_results: int = 10,
        categories: list[str] | None = None,
    ) -> list[ArxivPaper]:
        """Search papers using the core client."""
        # Map parameters to core format
        if categories:
            cat_query = " OR ".join([f"cat:{c}" for c in categories])
            full_query = f"({query}) AND ({cat_query})"
        else:
            full_query = query

        core_papers = self._core_client.search(full_query, max_results=max_results)
        return [ArxivPaper.from_core(p) for p in core_papers]

    def get_paper(self, arxiv_id: str) -> ArxivPaper | None:
        """Get paper details by arXiv ID (legacy name)."""
        core_paper = self._core_client.get_paper(arxiv_id)
        if core_paper is None:
            return None
        return ArxivPaper.from_core(core_paper)

    def fetch(self, arxiv_id: str) -> ArxivPaper | None:
        """Backward-compatible alias for get_paper()."""
        return self.get_paper(arxiv_id)
