"""CrossRef resolver for DOI-based metadata lookup.

This module provides:
- resolve_crossref(): Look up metadata from CrossRef API

Per RP22, this enriches Reference with DOI, title, authors, year.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..reference import Reference

logger = logging.getLogger("jarvis_core.resolvers.crossref")

# CrossRef API endpoint
CROSSREF_API = "https://api.crossref.org/works"


@dataclass
class CrossRefResult:
    """Result from CrossRef lookup."""

    doi: str | None = None
    title: str | None = None
    authors: list[str] | None = None
    year: int | None = None
    journal: str | None = None
    url: str | None = None
    success: bool = False


def _extract_title_from_locator(locator: str) -> str | None:
    """Try to extract a searchable title from locator."""
    # For PDF: extract filename without extension
    if locator.startswith("pdf:"):
        match = re.search(r"pdf:(.+?)(?:#|$)", locator)
        if match:
            path = match.group(1)
            # Get filename without path and extension
            filename = path.split("/")[-1].split("\\")[-1]
            name = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
            # Clean up common patterns
            name = re.sub(r"[-_]+", " ", name)
            return name if len(name) > 3 else None
    return None


def search_crossref(query: str, timeout: float = 5.0) -> CrossRefResult:
    """Search CrossRef API for a query string.

    Args:
        query: Search query (title, DOI, etc.)
        timeout: Request timeout in seconds.

    Returns:
        CrossRefResult with metadata if found.
    """
    result = CrossRefResult()

    try:
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        url = f"{CROSSREF_API}?query={encoded_query}&rows=1"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Jarvis-Evidence-QA/1.0 (mailto:research@example.com)"},
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") == "ok":
            items = data.get("message", {}).get("items", [])
            if items:
                item = items[0]

                # Extract DOI
                result.doi = item.get("DOI")

                # Extract title
                titles = item.get("title", [])
                if titles:
                    result.title = titles[0]

                # Extract authors
                authors_raw = item.get("author", [])
                result.authors = []
                for author in authors_raw:
                    family = author.get("family", "")
                    given = author.get("given", "")
                    if family:
                        name = f"{family}, {given}" if given else family
                        result.authors.append(name)

                # Extract year
                published = item.get("published-print") or item.get("published-online")
                if published:
                    date_parts = published.get("date-parts", [[]])
                    if date_parts and date_parts[0]:
                        result.year = date_parts[0][0]

                # Extract journal
                container = item.get("container-title", [])
                if container:
                    result.journal = container[0]

                # Extract URL
                result.url = item.get("URL")

                result.success = True

    except Exception as e:
        logger.warning(f"CrossRef lookup failed for '{query}': {e}")

    return result


def resolve_crossref(ref: Reference, timeout: float = 5.0) -> Reference:
    """Resolve Reference metadata using CrossRef.

    Attempts to enrich the Reference with DOI, title, authors, year.

    Args:
        ref: Reference to enrich.
        timeout: Request timeout.

    Returns:
        Updated Reference (same object, mutated).
    """
    # Skip if already has DOI
    if hasattr(ref, "doi") and ref.doi:
        return ref

    # Try to get a search query
    query = ref.title or _extract_title_from_locator(ref.locator)
    if not query:
        return ref

    result = search_crossref(query, timeout)

    if result.success:
        # Update reference with found metadata
        if result.doi and not getattr(ref, "doi", None):
            ref.doi = result.doi
        if result.title and not ref.title:
            ref.title = result.title
        if result.authors and not ref.authors:
            ref.authors = result.authors
        if result.year and not ref.year:
            ref.year = result.year
        if result.journal and not getattr(ref, "journal", None):
            ref.journal = result.journal

    return ref
