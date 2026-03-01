"""Semantic Scholar Client for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.4: Free API integration.
Uses Semantic Scholar Academic Graph API (free tier: 100 requests/5 min).

A-2: Added exponential backoff retry on 429 Too Many Requests.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

S2_API_BASE = "https://api.semanticscholar.org/graph/v1"

# A-2: Retry configuration for 429 errors
RETRY_WAIT_SECONDS = [5, 10, 30]  # Exponential backoff: 5s, 10s, 30s
MAX_RETRIES = len(RETRY_WAIT_SECONDS)


@dataclass
class S2Author:
    """Semantic Scholar author."""

    author_id: str
    name: str


@dataclass
class S2Paper:
    """Semantic Scholar paper representation."""

    paper_id: str
    title: str
    abstract: str = ""
    authors: list[S2Author] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    citation_count: int = 0
    reference_count: int = 0
    doi: str | None = None
    arxiv_id: str | None = None
    url: str = ""
    fields_of_study: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": [{"id": a.author_id, "name": a.name} for a in self.authors],
            "year": self.year,
            "venue": self.venue,
            "citation_count": self.citation_count,
            "reference_count": self.reference_count,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "url": self.url,
            "fields_of_study": self.fields_of_study,
        }


class SemanticScholarClient:
    """Client for Semantic Scholar Academic Graph API.

    Free tier: 100 requests per 5 minutes.
    A-2: Includes exponential backoff retry on 429 errors.
    """

    PAPER_FIELDS = [
        "paperId",
        "title",
        "abstract",
        "authors",
        "year",
        "venue",
        "citationCount",
        "referenceCount",
        "externalIds",
        "url",
        "fieldsOfStudy",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        rate_limit: float = 3.0,  # ~100 per 5 min = 20/min = 1 per 3 sec
    ):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._session = requests.Session()

        if api_key:
            self._session.headers["x-api-key"] = api_key

    def _rate_limit_wait(self) -> None:
        """Wait for rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, url: str, params: dict, timeout: int = 30) -> dict | None:
        """Make an HTTP GET request with 429 retry logic (A-2).

        Args:
            url: Request URL.
            params: Query parameters.
            timeout: Request timeout in seconds.

        Returns:
            Parsed JSON dict, or None on failure.
        """
        self._rate_limit_wait()

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self._session.get(url, params=params, timeout=timeout)

                # A-2: Handle 429 Too Many Requests with exponential backoff
                if response.status_code == 429:
                    if attempt < MAX_RETRIES:
                        wait = RETRY_WAIT_SECONDS[attempt]
                        logger.warning(
                            f"S2 rate limit hit (429). "
                            f"Retry {attempt + 1}/{MAX_RETRIES} in {wait}s..."
                        )
                        print(
                            f"    S2 rate limit (429). "
                            f"Waiting {wait}s before retry "
                            f"({attempt + 1}/{MAX_RETRIES})..."
                        )
                        time.sleep(wait)
                        continue
                    else:
                        logger.error(
                            f"S2 rate limit (429) exceeded after "
                            f"{MAX_RETRIES} retries. Giving up."
                        )
                        print(
                            f"    S2 rate limit: all {MAX_RETRIES} "
                            f"retries exhausted. Returning empty."
                        )
                        return None

                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                if attempt < MAX_RETRIES and "429" in str(e):
                    wait = RETRY_WAIT_SECONDS[attempt]
                    logger.warning(f"S2 request error (retrying in {wait}s): {e}")
                    print(f"    S2 error (retrying in {wait}s): {e}")
                    time.sleep(wait)
                    continue
                logger.error(f"S2 request error: {e}")
                return None

        return None

    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        year: str | None = None,
        fields_of_study: list[str] | None = None,
    ) -> list[S2Paper]:
        """Search for papers.

        Args:
            query: Search query.
            limit: Maximum results (max 100).
            offset: Result offset for pagination.
            year: Year filter (e.g., "2020-2024").
            fields_of_study: Field filter.

        Returns:
            List of S2Paper objects.
        """
        url = f"{S2_API_BASE}/paper/search"
        params = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
            "fields": ",".join(self.PAPER_FIELDS),
        }

        if year:
            params["year"] = year
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)

        data = self._make_request(url, params, timeout=30)
        if data is None:
            return []

        papers = [self._parse_paper(p) for p in data.get("data", [])]
        logger.info(f"S2 search '{query[:50]}...' returned {len(papers)} results")
        return papers

    def get_paper(self, paper_id: str) -> S2Paper | None:
        """Get paper by ID.

        Args:
            paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID.
                     E.g., "10.1234/example" or "arXiv:2001.00001"

        Returns:
            S2Paper or None.
        """
        url = f"{S2_API_BASE}/paper/{paper_id}"
        params = {"fields": ",".join(self.PAPER_FIELDS)}

        data = self._make_request(url, params, timeout=30)
        if data is None:
            return None

        return self._parse_paper(data)

    def get_citations(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[S2Paper]:
        """Get papers that cite this paper.

        Args:
            paper_id: Source paper ID.
            limit: Maximum results.

        Returns:
            List of citing papers.
        """
        url = f"{S2_API_BASE}/paper/{paper_id}/citations"
        params = {
            "fields": ",".join(self.PAPER_FIELDS),
            "limit": min(limit, 1000),
        }

        data = self._make_request(url, params, timeout=60)
        if data is None:
            return []

        papers = []
        for item in data.get("data", []):
            citing = item.get("citingPaper")
            if citing:
                papers.append(self._parse_paper(citing))

        return papers

    def get_references(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[S2Paper]:
        """Get papers referenced by this paper.

        Args:
            paper_id: Source paper ID.
            limit: Maximum results.

        Returns:
            List of referenced papers.
        """
        url = f"{S2_API_BASE}/paper/{paper_id}/references"
        params = {
            "fields": ",".join(self.PAPER_FIELDS),
            "limit": min(limit, 1000),
        }

        data = self._make_request(url, params, timeout=60)
        if data is None:
            return []

        papers = []
        for item in data.get("data", []):
            cited = item.get("citedPaper")
            if cited:
                papers.append(self._parse_paper(cited))

        return papers

    def _parse_paper(self, data: dict[str, Any]) -> S2Paper:
        """Parse paper from API response."""
        authors = []
        for a in data.get("authors", []):
            authors.append(
                S2Author(
                    author_id=a.get("authorId", ""),
                    name=a.get("name", ""),
                )
            )

        external_ids = data.get("externalIds", {}) or {}

        return S2Paper(
            paper_id=data.get("paperId", ""),
            title=data.get("title", ""),
            abstract=data.get("abstract", "") or "",
            authors=authors,
            year=data.get("year"),
            venue=data.get("venue", "") or "",
            citation_count=data.get("citationCount", 0) or 0,
            reference_count=data.get("referenceCount", 0) or 0,
            doi=external_ids.get("DOI"),
            arxiv_id=external_ids.get("ArXiv"),
            url=data.get("url", ""),
            fields_of_study=data.get("fieldsOfStudy", []) or [],
        )
