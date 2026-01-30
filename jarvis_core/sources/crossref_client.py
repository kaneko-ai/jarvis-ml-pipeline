"""Crossref API Client.

Free API client for Crossref metadata retrieval.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.4.5
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

CROSSREF_BASE_URL = "https://api.crossref.org"


@dataclass
class CrossrefWork:
    """Represents a work from Crossref."""

    doi: str
    title: str
    authors: list[str] = field(default_factory=list)
    published_date: datetime | None = None
    journal: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publisher: str | None = None
    abstract: str | None = None
    type: str | None = None  # e.g., "journal-article"
    issn: list[str] = field(default_factory=list)
    url: str | None = None
    references_count: int = 0
    cited_by_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "journal": self.journal,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "publisher": self.publisher,
            "abstract": self.abstract,
            "type": self.type,
            "issn": self.issn,
            "url": self.url,
            "references_count": self.references_count,
            "cited_by_count": self.cited_by_count,
        }


class CrossrefClient:
    """Client for the Crossref API.

    Provides DOI resolution and metadata retrieval.

    Example:
        >>> client = CrossrefClient(mailto="your@email.com")
        >>> work = client.get_work("10.1038/nature12373")
        >>> print(work.title)
    """

    def __init__(
        self,
        mailto: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the Crossref client.

        Args:
            mailto: Email for "polite pool" access (faster rate limits)
            timeout: Request timeout in seconds
        """
        self._mailto = mailto
        self._timeout = timeout
        self._headers = {
            "User-Agent": (
                f"JARVIS Research OS/1.0 (mailto:{mailto})" if mailto else "JARVIS Research OS/1.0"
            ),
        }

    def get_work(self, doi: str) -> CrossrefWork | None:
        """Get metadata for a DOI.

        Args:
            doi: DOI to look up

        Returns:
            CrossrefWork or None if not found
        """
        # Clean the DOI
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        doi = doi.strip()

        url = f"{CROSSREF_BASE_URL}/works/{doi}"

        try:
            response = requests.get(url, timeout=self._timeout, headers=self._headers)

            if response.status_code == 404:
                logger.warning(f"DOI not found: {doi}")
                return None

            response.raise_for_status()
            data = response.json()

            return self._parse_work(data.get("message", {}))

        except requests.RequestException as e:
            logger.error(f"Crossref API request failed for {doi}: {e}")
            return None

    def search(
        self,
        query: str,
        rows: int = 10,
        offset: int = 0,
        filter_type: str | None = None,
    ) -> list[CrossrefWork]:
        """Search for works.

        Args:
            query: Search query
            rows: Number of results (max 1000)
            offset: Starting offset
            filter_type: Filter by type (e.g., "journal-article")

        Returns:
            List of CrossrefWork objects
        """
        params = {
            "query": query,
            "rows": str(min(rows, 1000)),
            "offset": str(offset),
        }

        if filter_type:
            params["filter"] = f"type:{filter_type}"

        url = f"{CROSSREF_BASE_URL}/works"

        try:
            response = requests.get(
                url, params=params, timeout=self._timeout, headers=self._headers
            )
            response.raise_for_status()
            data = response.json()

            works = []
            for item in data.get("message", {}).get("items", []):
                work = self._parse_work(item)
                if work:
                    works.append(work)

            return works

        except requests.RequestException as e:
            logger.error(f"Crossref search failed: {e}")
            return []

    def _parse_work(self, item: dict[str, Any]) -> CrossrefWork | None:
        """Parse a Crossref work item."""
        try:
            doi = item.get("DOI", "")
            if not doi:
                return None

            # Title
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""

            # Authors
            authors = []
            for author in item.get("author", []):
                name_parts = []
                if author.get("given"):
                    name_parts.append(author["given"])
                if author.get("family"):
                    name_parts.append(author["family"])
                if name_parts:
                    authors.append(" ".join(name_parts))

            # Published date
            published_date = None
            date_parts = item.get("published-print", {}).get("date-parts", [[]])
            if not date_parts or not date_parts[0]:
                date_parts = item.get("published-online", {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                year = parts[0] if len(parts) > 0 else 2000
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                try:
                    published_date = datetime(year, month, day)
                except ValueError as e:
                    logger.debug(f"Failed to parse published date {year}-{month}-{day}: {e}")

            # Journal
            container = item.get("container-title", [])
            journal = container[0] if container else None

            # Abstract
            abstract = item.get("abstract", "")
            if abstract:
                # Remove JATS tags
                abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "")
                abstract = abstract.replace("<jats:title>", "").replace("</jats:title>", "")

            return CrossrefWork(
                doi=doi,
                title=title,
                authors=authors,
                published_date=published_date,
                journal=journal,
                volume=item.get("volume"),
                issue=item.get("issue"),
                pages=item.get("page"),
                publisher=item.get("publisher"),
                abstract=abstract if abstract else None,
                type=item.get("type"),
                issn=item.get("ISSN", []),
                url=item.get("URL"),
                references_count=item.get("references-count", 0),
                cited_by_count=item.get("is-referenced-by-count", 0),
            )

        except Exception as e:
            logger.error(f"Failed to parse Crossref work: {e}")
            return None