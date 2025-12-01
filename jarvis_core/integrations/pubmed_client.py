from __future__ import annotations

"""Lightweight PubMed client helpers for literature agents."""

import logging
from typing import Any, List, TYPE_CHECKING
from xml.etree import ElementTree

import requests

logger = logging.getLogger("jarvis_core.integrations.pubmed")

if TYPE_CHECKING:
    from jarvis_core.agents.literature import PaperSummary

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_pubmed(query: str, max_results: int = 20) -> List[str]:
    """Search PubMed via ESearch and return a list of PMIDs."""

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "pub+date",
    }
    try:
        resp = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        ids = payload.get("esearchresult", {}).get("idlist", [])
        return [pmid for pmid in ids if pmid]
    except Exception as exc:  # pragma: no cover - network failures
        logger.warning("PubMed search failed for query '%s': %s", query, exc)
        return []


def fetch_pubmed_details(pmids: List[str]) -> List["PaperSummary"]:
    """Fetch PubMed article metadata via EFetch and return parsed summaries."""

    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    try:
        resp = requests.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover - network failures
        logger.warning("PubMed fetch failed for pmids %s: %s", pmids, exc)
        return []

    from jarvis_core.agents.literature import PaperSummary  # Local import to avoid circular imports

    try:
        root = ElementTree.fromstring(resp.text)
    except ElementTree.ParseError as exc:  # pragma: no cover - malformed xml
        logger.warning("Failed to parse PubMed XML: %s", exc)
        return []

    summaries: List[PaperSummary] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = (article.findtext(".//PMID") or "").strip()
        title = (article.findtext(".//ArticleTitle") or "").strip()
        journal = (article.findtext(".//Journal/Title") or "").strip()

        year_text = (article.findtext(".//PubDate/Year") or "").strip()
        try:
            year = int(year_text)
        except ValueError:
            year = None

        doi = None
        for art_id in article.findall(".//ArticleIdList/ArticleId"):
            if art_id.attrib.get("IdType") == "doi":
                doi = (art_id.text or "").strip()
                break

        abstract_parts = [part.text or "" for part in article.findall(".//Abstract/AbstractText")]
        abstract = "\n".join([p for p in abstract_parts if p]).strip() or None

        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

        summary = PaperSummary(
            pmid=pmid,
            title=title,
            journal=journal,
            year=year,
            doi=doi,
            url=url,
            abstract=abstract,
            score=0.0,
        )
        summaries.append(summary)

    logger.info("Fetched %d PubMed summaries", len(summaries))
    return summaries
