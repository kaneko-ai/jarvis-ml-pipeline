"""Citation enricher: fetch reference/citation data from S2 and build graph.

Queries Semantic Scholar API to get references and cited-by for each paper,
then builds a CitationGraph with real edges.
"""
from __future__ import annotations

import json
import time
import requests
from pathlib import Path
from typing import Optional

from jarvis_core.rag.citation_graph import CitationGraph

S2_API = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "paperId,externalIds,title,year,authors"
RATE_DELAY = 1.2  # seconds between S2 requests (100 req/5min limit)


def _s2_get(url: str, params: dict = None, retries: int = 3) -> Optional[dict]:
    """GET from S2 API with retry on 429."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"  [S2] 429 rate limit, waiting {wait}s ...")
                time.sleep(wait)
                continue
            print(f"  [S2] HTTP {resp.status_code} for {url}")
            return None
        except Exception as e:
            print(f"  [S2] Error: {e}")
            return None
    return None


def _find_s2_paper_id(paper: dict) -> Optional[str]:
    """Try to find S2 paper ID from DOI, PMID, or title search."""
    doi = paper.get("doi", "")
    if doi:
        data = _s2_get(f"{S2_API}/paper/DOI:{doi}", {"fields": "paperId"})
        if data and data.get("paperId"):
            return data["paperId"]
        time.sleep(RATE_DELAY)

    pmid = paper.get("pmid", "")
    if pmid:
        data = _s2_get(f"{S2_API}/paper/PMID:{pmid}", {"fields": "paperId"})
        if data and data.get("paperId"):
            return data["paperId"]
        time.sleep(RATE_DELAY)

    title = paper.get("title", "")
    if title:
        data = _s2_get(f"{S2_API}/paper/search", {"query": title[:200], "limit": 1, "fields": "paperId,title"})
        if data and data.get("data") and len(data["data"]) > 0:
            return data["data"][0]["paperId"]
        time.sleep(RATE_DELAY)

    return None


def enrich_papers_with_citations(
    papers: list[dict],
    max_refs: int = 10,
    max_citations: int = 10,
) -> list[dict]:
    """Fetch references and citations from S2 for each paper.

    Returns enriched paper list with 'references' and 'cited_by' fields.
    """
    enriched = []
    total = len(papers)

    for idx, paper in enumerate(papers):
        print(f"  [{idx+1}/{total}] {paper.get('title', 'unknown')[:60]} ...")
        s2_id = _find_s2_paper_id(paper)

        if not s2_id:
            print(f"    S2 ID not found, skipping")
            enriched.append(paper)
            continue

        paper["s2_paper_id"] = s2_id

        # Fetch references
        time.sleep(RATE_DELAY)
        ref_data = _s2_get(
            f"{S2_API}/paper/{s2_id}/references",
            {"fields": S2_FIELDS, "limit": max_refs}
        )
        refs = []
        if ref_data and ref_data.get("data"):
            for item in ref_data["data"]:
                cp = item.get("citedPaper", {})
                if cp and cp.get("paperId"):
                    refs.append({
                        "paperId": cp["paperId"],
                        "doi": (cp.get("externalIds") or {}).get("DOI", ""),
                        "title": cp.get("title", ""),
                        "year": cp.get("year"),
                    })
        paper["references"] = refs
        print(f"    refs: {len(refs)}")

        # Fetch citations (cited-by)
        time.sleep(RATE_DELAY)
        cit_data = _s2_get(
            f"{S2_API}/paper/{s2_id}/citations",
            {"fields": S2_FIELDS, "limit": max_citations}
        )
        cited_by = []
        if cit_data and cit_data.get("data"):
            for item in cit_data["data"]:
                cp = item.get("citingPaper", {})
                if cp and cp.get("paperId"):
                    cited_by.append({
                        "paperId": cp["paperId"],
                        "doi": (cp.get("externalIds") or {}).get("DOI", ""),
                        "title": cp.get("title", ""),
                        "year": cp.get("year"),
                    })
        paper["cited_by"] = cited_by
        print(f"    cited_by: {len(cited_by)}")

        enriched.append(paper)

    return enriched


def build_enriched_graph(
    json_path: str,
    max_refs: int = 10,
    max_citations: int = 10,
    save_dir: Optional[str] = None,
) -> CitationGraph:
    """Load papers from JSON, enrich with S2 data, build CitationGraph.

    Args:
        json_path: JARVIS JSON file with papers
        max_refs: max references per paper to fetch
        max_citations: max citing papers per paper to fetch
        save_dir: if provided, save enriched JSON and graph files

    Returns:
        CitationGraph with nodes and edges
    """
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    papers = data if isinstance(data, list) else data.get("papers", [])

    print(f"[citation-enricher] Enriching {len(papers)} papers with S2 data ...")
    enriched = enrich_papers_with_citations(papers, max_refs, max_citations)

    cg = CitationGraph()
    cg.add_papers(enriched)
    edge_count = cg.add_citations_from_s2(enriched)

    stats = cg.stats()
    print(f"[citation-enricher] Graph: {stats['nodes']} nodes, {stats['edges']} edges")

    if save_dir:
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Save enriched JSON
        ej_path = out / "enriched_papers.json"
        ej_path.write_text(
            json.dumps(enriched, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[citation-enricher] Enriched JSON: {ej_path}")

        # Save graph files
        paths = cg.save(str(out), prefix="citation_network")
        for kind, path in paths.items():
            print(f"  {kind}: {path}")

    return cg
