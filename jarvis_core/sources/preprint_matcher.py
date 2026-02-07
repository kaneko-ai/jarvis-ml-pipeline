"""Match preprints to published versions via Crossref."""

from __future__ import annotations

from dataclasses import dataclass

import requests  # type: ignore[import-untyped]


@dataclass
class PublishedVersion:
    doi: str
    journal: str | None
    publication_date: str | None
    changes_summary: str | None


def find_published_version(preprint_id: str) -> PublishedVersion | None:
    """Find a published version for a preprint ID.

    Supports arXiv, bioRxiv, and medRxiv identifiers.
    """
    query = preprint_id
    if "arxiv" in preprint_id.lower():
        query = preprint_id.replace("arXiv:", "").strip()

    url = "https://api.crossref.org/works"
    params = {
        "query.bibliographic": query,
        "rows": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("message", {}).get("items", [])
        if not items:
            return None
        item = items[0]
        date_parts = item.get("published-print", {}).get("date-parts") or item.get(
            "published-online", {}
        ).get("date-parts")
        publication_date = "-".join(str(p) for p in date_parts[0]) if date_parts else None
        return PublishedVersion(
            doi=item.get("DOI", ""),
            journal=(item.get("container-title") or [None])[0],
            publication_date=publication_date,
            changes_summary="Crossref match",
        )
    except requests.RequestException:
        return None
