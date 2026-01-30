"""PubMed resolver for PMID-based metadata lookup.

This module provides:
- resolve_pubmed(): Look up metadata from PubMed API

Per RP22, this enriches Reference with PMID, title, authors, year.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..reference import Reference

logger = logging.getLogger("jarvis_core.resolvers.pubmed")

# PubMed E-utilities endpoints
ESEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


@dataclass
class PubMedResult:
    """Result from PubMed lookup."""

    pmid: str | None = None
    title: str | None = None
    authors: list[str] | None = None
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    success: bool = False


def search_pubmed(query: str, timeout: float = 5.0) -> PubMedResult:
    """Search PubMed for a query string.

    Args:
        query: Search query (title, PMID, etc.)
        timeout: Request timeout in seconds.

    Returns:
        PubMedResult with metadata if found.
    """
    result = PubMedResult()

    try:
        # First, search for the PMID
        search_url = f"{ESEARCH_API}?db=pubmed&term={query}&retmax=1&retmode=json"

        with urllib.request.urlopen(search_url, timeout=timeout) as response:
            search_data = json.loads(response.read().decode("utf-8"))

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return result

        pmid = id_list[0]
        result.pmid = pmid

        # Now get the summary
        summary_url = f"{ESUMMARY_API}?db=pubmed&id={pmid}&retmode=json"

        with urllib.request.urlopen(summary_url, timeout=timeout) as response:
            summary_data = json.loads(response.read().decode("utf-8"))

        doc = summary_data.get("result", {}).get(pmid, {})
        if doc:
            # Extract title
            result.title = doc.get("title")

            # Extract authors
            authors_raw = doc.get("authors", [])
            result.authors = [a.get("name", "") for a in authors_raw if a.get("name")]

            # Extract year from pubdate
            pubdate = doc.get("pubdate", "")
            year_match = re.search(r"(\d{4})", pubdate)
            if year_match:
                result.year = int(year_match.group(1))

            # Extract journal
            result.journal = doc.get("source")

            # Extract DOI from articleids
            for artid in doc.get("articleids", []):
                if artid.get("idtype") == "doi":
                    result.doi = artid.get("value")
                    break

            result.success = True

    except Exception as e:
        logger.warning(f"PubMed lookup failed for '{query}': {e}")

    return result


def resolve_pubmed(ref: Reference, timeout: float = 5.0) -> Reference:
    """Resolve Reference metadata using PubMed.

    Attempts to enrich the Reference with PMID, title, authors, year.

    Args:
        ref: Reference to enrich.
        timeout: Request timeout.

    Returns:
        Updated Reference (same object, mutated).
    """
    # Skip if already has PMID
    if hasattr(ref, "pmid") and ref.pmid:
        return ref

    # Use title as search query
    query = ref.title
    if not query:
        return ref

    result = search_pubmed(query, timeout)

    if result.success:
        # Update reference with found metadata
        if result.pmid and not getattr(ref, "pmid", None):
            ref.pmid = result.pmid
        if result.title and not ref.title:
            ref.title = result.title
        if result.authors and not ref.authors:
            ref.authors = result.authors
        if result.year and not ref.year:
            ref.year = result.year
        if result.journal and not getattr(ref, "journal", None):
            ref.journal = result.journal
        if result.doi and not getattr(ref, "doi", None):
            ref.doi = result.doi

    return ref