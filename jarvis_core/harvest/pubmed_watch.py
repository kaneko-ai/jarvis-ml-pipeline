"""PubMed watcher for harvest watch mode."""

from __future__ import annotations

from jarvis_core.sources.pubmed_client import PubMedClient


def watch_pubmed(*, since_hours: int, max_items: int, query: str) -> tuple[list[dict], list[dict]]:
    client = PubMedClient()
    warnings: list[dict] = []
    pmids = client.search(query=query, max_results=max_items, sort="date")
    if not pmids:
        return [], [
            {
                "code": "WATCH_EMPTY",
                "msg": "No PubMed records found for watch query.",
                "severity": "warning",
            }
        ]

    articles = client.fetch(pmids[:max_items])
    items: list[dict] = []
    for article in articles:
        paper_key = f"pmid:{article.pmid}"
        items.append(
            {
                "paper_key": paper_key,
                "source": "pubmed",
                "pmid": article.pmid,
                "doi": article.doi,
                "title": article.title,
                "journal": article.journal,
                "pub_date": article.pub_date,
                "pmc_id": article.pmc_id,
                "metadata": article.to_dict(),
            }
        )
    return items, warnings
