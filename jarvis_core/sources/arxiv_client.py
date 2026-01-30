"""arXiv API Client.

Free API client for arXiv paper search and retrieval.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.4.4
"""

from __future__ import annotations

import logging
import time
import defusedxml.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

# arXiv API constants
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
ARXIV_PDF_BASE = "https://arxiv.org/pdf"
ARXIV_ABS_BASE = "https://arxiv.org/abs"

# Namespace for Atom feed
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


@dataclass
class ArxivPaper:
    """Represents an arXiv paper."""

    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    published: datetime | None = None
    updated: datetime | None = None
    categories: list[str] = field(default_factory=list)
    primary_category: str | None = None
    doi: str | None = None
    journal_ref: str | None = None
    pdf_url: str | None = None
    abs_url: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "published": self.published.isoformat() if self.published else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "categories": self.categories,
            "primary_category": self.primary_category,
            "doi": self.doi,
            "journal_ref": self.journal_ref,
            "pdf_url": self.pdf_url,
            "abs_url": self.abs_url,
        }


class ArxivClient:
    """Client for the arXiv API.

    Provides search and paper retrieval functionality.
    Respects arXiv rate limits (3 second delay between requests).

    Example:
        >>> client = ArxivClient()
        >>> papers = client.search("machine learning cancer", max_results=10)
        >>> for paper in papers:
        ...     print(paper.title)
    """

    def __init__(
        self,
        timeout: float = 30.0,
        rate_limit_delay: float = 3.0,
    ):
        """Initialize the arXiv client.

        Args:
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between requests (arXiv recommends 3s)
        """
        self._timeout = timeout
        self._rate_limit_delay = rate_limit_delay
        self._last_request_time: float | None = None

    def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limit."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._rate_limit_delay:
                time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def search(
        self,
        query: str,
        max_results: int = 10,
        start: int = 0,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> list[ArxivPaper]:
        """Search for papers on arXiv.

        Args:
            query: Search query (supports arXiv query syntax)
            max_results: Maximum number of results (max 1000)
            start: Starting index for pagination
            sort_by: Sort field ("relevance", "lastUpdatedDate", "submittedDate")
            sort_order: Sort order ("ascending", "descending")

        Returns:
            List of ArxivPaper objects
        """
        self._wait_for_rate_limit()

        # Build query URL
        params = {
            "search_query": f"all:{quote_plus(query)}",
            "start": str(start),
            "max_results": str(min(max_results, 1000)),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        url = f"{ARXIV_BASE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        try:
            response = requests.get(url, timeout=self._timeout)
            response.raise_for_status()

            return self._parse_response(response.text)

        except requests.RequestException as e:
            logger.error(f"arXiv API request failed: {e}")
            return []

    def get_paper(self, arxiv_id: str) -> ArxivPaper | None:
        """Get a specific paper by arXiv ID.

        Args:
            arxiv_id: arXiv paper ID (e.g., "2101.00001" or "hep-th/9901001")

        Returns:
            ArxivPaper or None if not found
        """
        self._wait_for_rate_limit()

        # Clean the ID
        arxiv_id = arxiv_id.replace("arXiv:", "").strip()

        url = f"{ARXIV_BASE_URL}?id_list={arxiv_id}"

        try:
            response = requests.get(url, timeout=self._timeout)
            response.raise_for_status()

            papers = self._parse_response(response.text)
            return papers[0] if papers else None

        except requests.RequestException as e:
            logger.error(f"arXiv API request failed for {arxiv_id}: {e}")
            return None

    def search_by_category(
        self,
        category: str,
        query: str | None = None,
        max_results: int = 10,
    ) -> list[ArxivPaper]:
        """Search within a specific arXiv category.

        Args:
            category: arXiv category (e.g., "cs.LG", "q-bio.NC")
            query: Additional search query
            max_results: Maximum number of results

        Returns:
            List of ArxivPaper objects
        """
        if query:
            full_query = f"cat:{category} AND all:{query}"
        else:
            full_query = f"cat:{category}"

        return self.search(full_query, max_results=max_results)

    def _parse_response(self, xml_content: str) -> list[ArxivPaper]:
        """Parse arXiv API XML response."""
        papers = []

        try:
            root = ET.fromstring(xml_content)

            for entry in root.findall(f"{ATOM_NS}entry"):
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"Failed to parse arXiv response: {e}")

        return papers

    def _parse_entry(self, entry: ET.Element) -> ArxivPaper | None:
        """Parse a single entry element."""
        try:
            # Extract ID
            id_elem = entry.find(f"{ATOM_NS}id")
            if id_elem is None or id_elem.text is None:
                return None

            # Extract arXiv ID from URL
            full_id = id_elem.text
            arxiv_id = full_id.split("/abs/")[-1] if "/abs/" in full_id else full_id.split("/")[-1]

            # Remove version suffix for clean ID
            base_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

            # Title
            title_elem = entry.find(f"{ATOM_NS}title")
            title = (
                title_elem.text.strip().replace("\n", " ")
                if title_elem is not None and title_elem.text
                else ""
            )

            # Abstract
            summary_elem = entry.find(f"{ATOM_NS}summary")
            abstract = (
                summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
            )

            # Authors
            authors = []
            for author in entry.findall(f"{ATOM_NS}author"):
                name_elem = author.find(f"{ATOM_NS}name")
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text)

            # Dates
            published = None
            published_elem = entry.find(f"{ATOM_NS}published")
            if published_elem is not None and published_elem.text:
                published = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))

            updated = None
            updated_elem = entry.find(f"{ATOM_NS}updated")
            if updated_elem is not None and updated_elem.text:
                updated = datetime.fromisoformat(updated_elem.text.replace("Z", "+00:00"))

            # Categories
            categories = []
            primary_category = None

            for category in entry.findall(f"{ATOM_NS}category"):
                term = category.get("term")
                if term:
                    categories.append(term)

            primary_cat = entry.find(f"{ARXIV_NS}primary_category")
            if primary_cat is not None:
                primary_category = primary_cat.get("term")

            # DOI
            doi = None
            doi_elem = entry.find(f"{ARXIV_NS}doi")
            if doi_elem is not None and doi_elem.text:
                doi = doi_elem.text

            # Journal reference
            journal_ref = None
            journal_elem = entry.find(f"{ARXIV_NS}journal_ref")
            if journal_elem is not None and journal_elem.text:
                journal_ref = journal_elem.text

            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                abstract=abstract,
                authors=authors,
                published=published,
                updated=updated,
                categories=categories,
                primary_category=primary_category,
                doi=doi,
                journal_ref=journal_ref,
                pdf_url=f"{ARXIV_PDF_BASE}/{base_id}.pdf",
                abs_url=f"{ARXIV_ABS_BASE}/{base_id}",
            )

        except Exception as e:
            logger.error(f"Failed to parse arXiv entry: {e}")
            return None

    def download_pdf(self, arxiv_id: str, output_path: str) -> bool:
        """Download PDF for an arXiv paper.

        Args:
            arxiv_id: arXiv paper ID
            output_path: Path to save the PDF

        Returns:
            True if download successful
        """
        self._wait_for_rate_limit()

        # Clean the ID
        arxiv_id = arxiv_id.replace("arXiv:", "").strip()
        base_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

        pdf_url = f"{ARXIV_PDF_BASE}/{base_id}.pdf"

        try:
            response = requests.get(pdf_url, timeout=60.0, allow_redirects=True)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded PDF: {arxiv_id} -> {output_path}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to download PDF for {arxiv_id}: {e}")
            return False