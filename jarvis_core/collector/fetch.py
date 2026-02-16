"""Local-first paper collector (metadata + optional OA PDF links)."""

from __future__ import annotations

from jarvis_core.sources.pubmed_client import PubMedClient
from jarvis_core.sources.unpaywall_client import UnpaywallClient


def collect_papers(*, query: str, max_items: int, oa_only: bool) -> tuple[list[dict], list[dict]]:
    warnings: list[dict] = []
    client = PubMedClient()
    pmids = client.search(query=query, max_results=max_items, sort="date")
    if not pmids:
        return [], [
            {"code": "COLLECT_EMPTY", "msg": "No papers found for query.", "severity": "warning"}
        ]
    articles = client.fetch(pmids[:max_items])

    unpaywall = UnpaywallClient(email="jarvis@example.invalid")
    papers: list[dict] = []
    for article in articles:
        oa_url = None
        is_oa = False
        if article.doi:
            try:
                oa = unpaywall.get_oa_status(article.doi)
            except Exception:
                oa = None
            if oa:
                is_oa = oa.is_oa
                oa_url = oa.best_oa_url
        if oa_only and not is_oa:
            continue
        papers.append(
            {
                "paper_key": f"pmid:{article.pmid}",
                "title": article.title,
                "doi": article.doi,
                "pmid": article.pmid,
                "journal": article.journal,
                "pub_date": article.pub_date,
                "oa": is_oa,
                "oa_url": oa_url,
                "metadata": article.to_dict(),
            }
        )
    if not papers:
        warnings.append(
            {
                "code": "OA_FILTER_EMPTY",
                "msg": "No OA papers matched the query.",
                "severity": "warning",
            }
        )
    return papers, warnings
