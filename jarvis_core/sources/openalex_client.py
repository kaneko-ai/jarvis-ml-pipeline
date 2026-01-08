"""OpenAlex Client for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.4: 無料API統合
Uses OpenAlex API (completely free, 100k requests/day).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests

logger = logging.getLogger(__name__)

OPENALEX_API_BASE = "https://api.openalex.org"


@dataclass
class OpenAlexWork:
    """OpenAlex work (paper) representation."""
    openalex_id: str
    title: str
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    publication_year: int | None = None
    publication_date: str = ""
    venue: str = ""
    cited_by_count: int = 0
    doi: str | None = None
    pmid: str | None = None
    concepts: list[str] = field(default_factory=list)
    open_access_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "openalex_id": self.openalex_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "publication_date": self.publication_date,
            "venue": self.venue,
            "cited_by_count": self.cited_by_count,
            "doi": self.doi,
            "pmid": self.pmid,
            "concepts": self.concepts,
            "open_access_url": self.open_access_url,
        }


class OpenAlexClient:
    """Client for OpenAlex API.
    
    Completely free, 100k requests per day with polite pool.
    """

    def __init__(
        self,
        email: str | None = None,
        rate_limit: float = 0.1,  # 10 requests/second
    ):
        self.email = email
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._session = requests.Session()

        # Polite pool with email gets higher rate limit
        if email:
            self._session.headers["User-Agent"] = f"JARVIS-Research-OS ({email})"

    def _rate_limit_wait(self) -> None:
        """Wait for rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _build_params(self, **kwargs) -> dict[str, Any]:
        """Build request parameters."""
        params = {k: v for k, v in kwargs.items() if v is not None}
        if self.email:
            params["mailto"] = self.email
        return params

    def search(
        self,
        query: str,
        per_page: int = 25,
        page: int = 1,
        filter_open_access: bool = False,
        from_year: int | None = None,
        to_year: int | None = None,
    ) -> list[OpenAlexWork]:
        """Search for works.
        
        Args:
            query: Search query.
            per_page: Results per page (max 200).
            page: Page number.
            filter_open_access: Only return open access works.
            from_year: Start year filter.
            to_year: End year filter.
            
        Returns:
            List of OpenAlexWork objects.
        """
        self._rate_limit_wait()

        url = f"{OPENALEX_API_BASE}/works"

        # Build filter
        filters = []
        if filter_open_access:
            filters.append("is_oa:true")
        if from_year:
            filters.append(f"from_publication_date:{from_year}-01-01")
        if to_year:
            filters.append(f"to_publication_date:{to_year}-12-31")

        params = self._build_params(
            search=query,
            per_page=min(per_page, 200),
            page=page,
            filter=",".join(filters) if filters else None,
        )

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            works = [self._parse_work(w) for w in data.get("results", [])]
            logger.info(f"OpenAlex search '{query[:50]}...' returned {len(works)} results")
            return works

        except requests.RequestException as e:
            logger.error(f"OpenAlex search error: {e}")
            return []

    def get_work(self, work_id: str) -> OpenAlexWork | None:
        """Get work by ID.
        
        Args:
            work_id: OpenAlex ID or DOI.
                    E.g., "W2741809807" or "https://doi.org/10.1234/example"
                    
        Returns:
            OpenAlexWork or None.
        """
        self._rate_limit_wait()

        # Handle DOI format
        if work_id.startswith("10."):
            work_id = f"https://doi.org/{work_id}"

        url = f"{OPENALEX_API_BASE}/works/{work_id}"
        params = self._build_params()

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_work(response.json())

        except requests.RequestException as e:
            logger.error(f"OpenAlex get work error: {e}")
            return None

    def get_citing_works(
        self,
        work_id: str,
        per_page: int = 25,
    ) -> list[OpenAlexWork]:
        """Get works that cite this work.
        
        Args:
            work_id: OpenAlex work ID.
            per_page: Results per page.
            
        Returns:
            List of citing works.
        """
        self._rate_limit_wait()

        url = f"{OPENALEX_API_BASE}/works"
        params = self._build_params(
            filter=f"cites:{work_id}",
            per_page=min(per_page, 200),
        )

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return [self._parse_work(w) for w in data.get("results", [])]

        except requests.RequestException as e:
            logger.error(f"OpenAlex citing works error: {e}")
            return []

    def get_related_works(
        self,
        work_id: str,
        per_page: int = 10,
    ) -> list[OpenAlexWork]:
        """Get related works.
        
        Args:
            work_id: OpenAlex work ID.
            per_page: Results per page.
            
        Returns:
            List of related works.
        """
        self._rate_limit_wait()

        url = f"{OPENALEX_API_BASE}/works/{work_id}/related_works"
        params = self._build_params(per_page=min(per_page, 200))

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return [self._parse_work(w) for w in data.get("results", [])]

        except requests.RequestException as e:
            logger.error(f"OpenAlex related works error: {e}")
            return []

    def _parse_work(self, data: dict[str, Any]) -> OpenAlexWork:
        """Parse work from API response."""
        # Extract authors
        authors = []
        for authorship in data.get("authorships", []):
            author = authorship.get("author", {})
            if author.get("display_name"):
                authors.append(author["display_name"])

        # Extract venue
        venue = ""
        locations = data.get("primary_location") or {}
        source = locations.get("source") or {}
        venue = source.get("display_name", "")

        # Extract concepts
        concepts = []
        for concept in data.get("concepts", [])[:5]:
            if concept.get("display_name"):
                concepts.append(concept["display_name"])

        # Extract IDs
        ids = data.get("ids", {})
        doi = ids.get("doi", "").replace("https://doi.org/", "") if ids.get("doi") else None
        pmid = ids.get("pmid", "").replace("https://pubmed.ncbi.nlm.nih.gov/", "") if ids.get("pmid") else None

        # Open access URL
        open_access = data.get("open_access", {})
        oa_url = open_access.get("oa_url")

        # Abstract (inverted index format)
        abstract = ""
        abstract_inverted = data.get("abstract_inverted_index", {})
        if abstract_inverted:
            # Reconstruct from inverted index
            word_positions = []
            for word, positions in abstract_inverted.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            abstract = " ".join(word for _, word in word_positions)

        return OpenAlexWork(
            openalex_id=data.get("id", "").replace("https://openalex.org/", ""),
            title=data.get("title", ""),
            abstract=abstract,
            authors=authors,
            publication_year=data.get("publication_year"),
            publication_date=data.get("publication_date", ""),
            venue=venue,
            cited_by_count=data.get("cited_by_count", 0),
            doi=doi,
            pmid=pmid,
            concepts=concepts,
            open_access_url=oa_url,
        )
