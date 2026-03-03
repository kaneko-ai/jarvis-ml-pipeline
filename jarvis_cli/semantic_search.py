"""jarvis semantic-search - ChromaDB persistent + legacy hybrid search."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


def run_semantic_search(args) -> int:
    """Run semantic search with ChromaDB persistence."""
    query = args.query
    top_k = args.top
    db_path = getattr(args, "db", None)
    index_only = getattr(args, "index_only", False)
    legacy = getattr(args, "legacy", False)

    # ------------------------------------------------------------------
    # Legacy mode: use old HybridSearch / keyword fallback (requires --db)
    # ------------------------------------------------------------------
    if legacy:
        if not db_path:
            print("  Error: --legacy requires --db <file.json>")
            return 1
        return _legacy_search(query, db_path, top_k)

    # ------------------------------------------------------------------
    # ChromaDB mode (default)
    # ------------------------------------------------------------------
    try:
        from jarvis_core.embeddings.paper_store import PaperStore
    except ImportError as e:
        print(f"  Error: ChromaDB not available ({e})")
        print("  Install with: python -m pip install chromadb")
        return 1

    store = PaperStore()

    # If --db is given, index that JSON file into ChromaDB first
    if db_path:
        p = Path(db_path)
        if not p.exists():
            print(f"  Error: File not found: {db_path}")
            return 1
        print(f"  Indexing {p.name} into ChromaDB...")
        count = store.add_from_json(str(p))
        print(f"  Indexed {count} papers (total in DB: {store.count()})")
        if index_only:
            print("  Done (--index-only mode).")
            return 0
        print()

    # Check if there are papers in the store
    total = store.count()
    if total == 0:
        print("  Error: ChromaDB is empty. Use --db <file.json> to index papers first.")
        return 1

    # Search
    print(f"  Query: {query}")
    print(f"  ChromaDB papers: {total}")
    start = time.time()
    results = store.search(query, top_k=top_k)
    elapsed = time.time() - start
    print(f"  Search completed in {elapsed:.2f}s")
    print()

    if not results:
        print("  No matching papers found.")
        return 0

    print(f"  Top {len(results)} results:")
    print(f"  {'Rank':<5} {'Score':>7} {'Title'}")
    print(f"  {'-'*4:<5} {'-'*7:>7} {'-'*55}")

    for rank, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        title = meta.get("title", r.get("id", "Unknown"))
        year = meta.get("year", "")
        source = meta.get("source", "")
        doi = meta.get("doi", "")
        score = r.get("score", 0)

        print(f"  {rank:<5} {score:>7.4f} {title}")
        details = []
        if year:
            details.append(f"Year: {year}")
        if source:
            details.append(f"Source: {source}")
        if doi:
            details.append(f"DOI: {doi}")
        if details:
            print(f"  {'':>13} {' | '.join(details)}")
        print()

    return 0


def _legacy_search(query: str, db_path: str, top_k: int) -> int:
    """Legacy in-memory HybridSearch / keyword fallback."""
    p = Path(db_path)
    if not p.exists():
        print(f"  Error: DB file not found: {p}")
        return 1

    with open(p, encoding="utf-8") as f:
        papers = json.load(f)

    if not papers:
        print("  Error: No papers in DB file.")
        return 1

    print(f"  [Legacy mode] Query: {query}")
    print(f"  DB: {p.name} ({len(papers)} papers)")
    print()

    corpus = []
    doc_ids = []
    metadata_list = []
    for i, paper in enumerate(papers):
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        text = f"{title}. {abstract}" if abstract else title
        corpus.append(text)
        doc_ids.append(str(i))
        metadata_list.append(paper)

    try:
        from jarvis_core.embeddings import HybridSearch

        print("  Building hybrid index (BM25 + SentenceTransformer)...")
        start = time.time()
        hybrid = HybridSearch()
        hybrid.index(corpus, ids=doc_ids, metadata=metadata_list)
        result = hybrid.search(query, top_k=top_k)
        search_results = result.results
        elapsed = time.time() - start

        print(f"  Search completed in {elapsed:.1f}s "
              f"(candidates: {result.total_candidates}, "
              f"fusion: {result.fusion_method})")
        print()

        if not search_results:
            print("  No matching papers found.")
            return 0

        print(f"  Top {len(search_results)} results:")
        print(f"  {'Rank':<5} {'Score':>6} {'Title'}")
        print(f"  {'-'*4:<5} {'-'*6:>6} {'-'*50}")

        for rank, sr in enumerate(search_results, 1):
            meta = sr.metadata if sr.metadata else {}
            title = meta.get("title", sr.text[:60])
            year = meta.get("year", "")
            source = meta.get("source", "")
            print(f"  {rank:<5} {sr.score:>6.4f} {title}")
            details = []
            if year:
                details.append(f"Year: {year}")
            if source:
                details.append(f"Source: {source}")
            if details:
                print(f"  {'':>12} {' | '.join(details)}")
            print()
        return 0

    except ImportError:
        print("  Falling back to keyword matching...")
        query_lower = query.lower()
        scored = []
        for i, text in enumerate(corpus):
            words = query_lower.split()
            matches = sum(1 for w in words if w in text.lower())
            if matches > 0:
                score = matches / len(words)
                scored.append((i, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:top_k]

        if not scored:
            print("  No matching papers found.")
            return 0

        print(f"  Top {len(scored)} results (keyword match):")
        for rank, (idx, score) in enumerate(scored, 1):
            title = papers[idx].get("title", "Unknown")
            print(f"  {rank}. [{score:.2f}] {title}")
        print()
        return 0
