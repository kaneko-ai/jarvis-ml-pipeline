"""PubMed API functions.

Per RP-04, extracted from run_pipeline.py for reuse.
"""

from __future__ import annotations

import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Optional

from .models import PaperRecord

# NCBI API key from environment
NCBI_API_KEY = os.environ.get("NCBI_API_KEY")


def pubmed_esearch(
    query: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_results: int = 50,
) -> List[str]:
    """Search PubMed and return list of PMIDs.

    Args:
        query: Search query.
        date_from: Start date (YYYY/MM/DD).
        date_to: End date (YYYY/MM/DD).
        max_results: Maximum results.

    Returns:
        List of PMIDs.
    """
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "xml",
        "sort": "relevance",
    }

    if date_from and date_to:
        params["mindate"] = date_from
        params["maxdate"] = date_to
        params["datetype"] = "pdat"

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = f"{base}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()

        root = ET.fromstring(data)
        pmids = [el.text for el in root.findall(".//Id") if el.text]
        return pmids

    except Exception as e:
        print(f"[pubmed_esearch] Error: {e}")
        return []


def pubmed_esummary(pmids: List[str]) -> List[PaperRecord]:
    """Get paper metadata for PMIDs.

    Args:
        pmids: List of PMIDs.

    Returns:
        List of PaperRecord objects.
    """
    if not pmids:
        return []

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = f"{base}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()

        root = ET.fromstring(data)
        records = []

        for docsum in root.findall(".//DocSum"):
            pmid = docsum.find("Id")
            pmid_text = pmid.text if pmid is not None else ""

            # Extract fields
            title = ""
            authors = []
            pubdate = ""
            journal = ""
            pmcid = ""
            doi = ""

            for item in docsum.findall("Item"):
                name = item.attrib.get("Name", "")
                if name == "Title":
                    title = item.text or ""
                elif name == "AuthorList":
                    authors = [a.text for a in item.findall("Item") if a.text]
                elif name == "PubDate":
                    pubdate = item.text or ""
                elif name == "FullJournalName":
                    journal = item.text or ""
                elif name == "ArticleIds":
                    for aid in item.findall("Item"):
                        aid_type = aid.attrib.get("Name", "")
                        if aid_type == "pmc" and aid.text:
                            pmcid = aid.text.replace("PMC", "")
                        elif aid_type == "doi" and aid.text:
                            doi = aid.text

            records.append(
                PaperRecord(
                    paper_id=pmid_text,
                    title=title,
                    authors=authors,
                    pubdate=pubdate,
                    journal=journal,
                    pmid=pmid_text,
                    pmcid=pmcid if pmcid else None,
                    doi=doi if doi else None,
                )
            )

        return records

    except Exception as e:
        print(f"[pubmed_esummary] Error: {e}")
        return []
