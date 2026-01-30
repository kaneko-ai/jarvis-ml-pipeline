"""Unified Source Client for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.4: 無料API統合
Provides a unified interface across all academic literature sources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .openalex_client import OpenAlexClient, OpenAlexWork
from .pubmed_client import PubMedArticle, PubMedClient
from .semantic_scholar_client import S2Paper, SemanticScholarClient

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Academic literature source types."""

    PUBMED = "pubmed"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    OPENALEX = "openalex"
    ARXIV = "arxiv"
    CROSSREF = "crossref"


@dataclass
class UnifiedPaper:
    """Unified paper representation across all sources."""

    id: str
    source: SourceType
    title: str
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str | None = None
    pmid: str | None = None
    citation_count: int = 0
    url: str | None = None
    keywords: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source.value,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "year": self.year,
            "venue": self.venue,
            "doi": self.doi,
            "pmid": self.pmid,
            "citation_count": self.citation_count,
            "url": self.url,
            "keywords": self.keywords,
        }

    @classmethod
    def from_pubmed(cls, article: PubMedArticle) -> UnifiedPaper:
        """Create from PubMed article."""
        year = None
        if article.pub_date:
            try:
                year = int(article.pub_date.split("-")[0])
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse publication year from '{article.pub_date}': {e}")

        return cls(
            id=f"pubmed:{article.pmid}",
            source=SourceType.PUBMED,
            title=article.title,
            abstract=article.abstract,
            authors=article.authors,
            year=year,
            venue=article.journal,
            doi=article.doi,
            pmid=article.pmid,
            keywords=article.mesh_terms,
            raw_data=article.to_dict(),
        )

    @classmethod
    def from_s2(cls, paper: S2Paper) -> UnifiedPaper:
        """Create from Semantic Scholar paper."""
        return cls(
            id=f"s2:{paper.paper_id}",
            source=SourceType.SEMANTIC_SCHOLAR,
            title=paper.title,
            abstract=paper.abstract,
            authors=[a.name for a in paper.authors],
            year=paper.year,
            venue=paper.venue,
            doi=paper.doi,
            citation_count=paper.citation_count,
            url=paper.url,
            keywords=paper.fields_of_study,
            raw_data=paper.to_dict(),
        )

    @classmethod
    def from_openalex(cls, work: OpenAlexWork) -> UnifiedPaper:
        """Create from OpenAlex work."""
        return cls(
            id=f"openalex:{work.openalex_id}",
            source=SourceType.OPENALEX,
            title=work.title,
            abstract=work.abstract,
            authors=work.authors,
            year=work.publication_year,
            venue=work.venue,
            doi=work.doi,
            pmid=work.pmid,
            citation_count=work.cited_by_count,
            url=work.open_access_url,
            keywords=work.concepts,
            raw_data=work.to_dict(),
        )


class UnifiedSourceClient:
    """Unified client for all academic literature sources.

    Provides:
    - Consistent interface across sources
    - Automatic fallback between sources
    - Deduplication by DOI
    - Aggregated search results
    """

    def __init__(
        self,
        email: str | None = None,
        pubmed_api_key: str | None = None,
        s2_api_key: str | None = None,
    ):
        self.pubmed = PubMedClient(
            api_key=pubmed_api_key,
            email=email,
        )
        self.s2 = SemanticScholarClient(
            api_key=s2_api_key,
        )
        self.openalex = OpenAlexClient(
            email=email,
        )

    def search(
        self,
        query: str,
        max_results: int = 20,
        sources: list[SourceType] | None = None,
        deduplicate: bool = True,
    ) -> list[UnifiedPaper]:
        """Search across multiple sources.

        Args:
            query: Search query.
            max_results: Max results per source.
            sources: Sources to search (default: all).
            deduplicate: Remove duplicates by DOI.

        Returns:
            List of UnifiedPaper objects.
        """
        if sources is None:
            sources = [
                SourceType.OPENALEX,  # Fastest, most comprehensive
                SourceType.SEMANTIC_SCHOLAR,
                SourceType.PUBMED,
            ]

        all_papers: list[UnifiedPaper] = []

        for source in sources:
            try:
                if source == SourceType.PUBMED:
                    articles = self.pubmed.search_and_fetch(query, max_results)
                    all_papers.extend(UnifiedPaper.from_pubmed(a) for a in articles)

                elif source == SourceType.SEMANTIC_SCHOLAR:
                    papers = self.s2.search(query, limit=max_results)
                    all_papers.extend(UnifiedPaper.from_s2(p) for p in papers)

                elif source == SourceType.OPENALEX:
                    works = self.openalex.search(query, per_page=max_results)
                    all_papers.extend(UnifiedPaper.from_openalex(w) for w in works)

            except Exception as e:
                logger.warning(f"Search failed for {source.value}: {e}")
                continue

        if deduplicate:
            all_papers = self._deduplicate(all_papers)

        return all_papers

    def get_by_doi(self, doi: str) -> UnifiedPaper | None:
        """Get paper by DOI.

        Tries multiple sources with fallback.
        """
        # Try OpenAlex first (fastest)
        try:
            work = self.openalex.get_work(doi)
            if work:
                return UnifiedPaper.from_openalex(work)
        except Exception as e:
            logger.debug(f"OpenAlex get_work failed for DOI {doi}: {e}")

        # Try Semantic Scholar
        try:
            paper = self.s2.get_paper(doi)
            if paper:
                return UnifiedPaper.from_s2(paper)
        except Exception as e:
            logger.debug(f"Semantic Scholar get_paper failed for DOI {doi}: {e}")

        return None

    def get_by_pmid(self, pmid: str) -> UnifiedPaper | None:
        """Get paper by PubMed ID."""
        try:
            articles = self.pubmed.fetch([pmid])
            if articles:
                return UnifiedPaper.from_pubmed(articles[0])
        except Exception as e:
            logger.debug(f"PubMed fetch failed for PMID {pmid}: {e}")
        return None

    def get_citations(
        self,
        paper: UnifiedPaper,
        max_results: int = 50,
    ) -> list[UnifiedPaper]:
        """Get papers that cite this paper.

        Uses the best available source based on paper metadata.
        """
        # Try to use DOI with Semantic Scholar or OpenAlex
        if paper.doi:
            try:
                # Semantic Scholar has better citation data
                papers = self.s2.get_citations(f"DOI:{paper.doi}", limit=max_results)
                return [UnifiedPaper.from_s2(p) for p in papers]
            except Exception as e:
                logger.debug(f"Semantic Scholar get_citations failed: {e}")

            try:
                works = self.openalex.get_citing_works(
                    f"https://doi.org/{paper.doi}",
                    per_page=max_results,
                )
                return [UnifiedPaper.from_openalex(w) for w in works]
            except Exception as e:
                logger.debug(f"OpenAlex get_citing_works failed: {e}")

        return []

    def _deduplicate(self, papers: list[UnifiedPaper]) -> list[UnifiedPaper]:
        """Remove duplicate papers by DOI."""
        seen_dois: set = set()
        unique_papers: list[UnifiedPaper] = []

        for paper in papers:
            if paper.doi:
                if paper.doi in seen_dois:
                    continue
                seen_dois.add(paper.doi)
            unique_papers.append(paper)

        return unique_papers

    def status(self) -> dict[str, Any]:
        """Get client status."""
        return {
            "sources": [s.value for s in SourceType],
            "pubmed_available": True,
            "semantic_scholar_available": True,
            "openalex_available": True,
        }
