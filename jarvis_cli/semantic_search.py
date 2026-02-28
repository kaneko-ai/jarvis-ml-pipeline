"""jarvis semantic-search - Hybrid Search (BM25 + Vector) over local paper DB."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


def run_semantic_search(args) -> int:
    """Run semantic search over a local JSON paper database."""
    query = args.query
    db_path = Path(args.db)
    top_k = args.top

    if not db_path.exists():
        print(f"  Error: DB file not found: {db_path}")
        return 1

    # Load papers
    with open(db_path, encoding="utf-8") as f:
        papers = json.load(f)

    if not papers:
        print("  Error: No papers in DB file.")
        return 1

    print(f"  Query: {query}")
    print(f"  DB: {db_path.name} ({len(papers)} papers)")
    print()

    # Build corpus: title + abstract for each paper
    corpus = []
    doc_ids = []
    metadata_list = []
    for i, p in enumerate(papers):
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        text = f"{title}. {abstract}" if abstract else title
        corpus.append(text)
        doc_ids.append(str(i))
        metadata_list.append(p)

    # Try HybridSearch (dense + sparse), fallback to BM25 only
    try:
        from jarvis_core.embeddings import HybridSearch

        print("  Building hybrid index (BM25 + SentenceTransformer)...")
        start = time.time()
        hybrid = HybridSearch()
        hybrid.index(corpus, ids=doc_ids, metadata=metadata_list)
        result = hybrid.search(query, top_k=top_k)

        # result is HybridSearchResult, actual items are in result.results
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
            evidence = meta.get("evidence_level", "")
            journal = meta.get("journal", "")

            print(f"  {rank:<5} {sr.score:>6.4f} {title}")
            details = []
            if year:
                details.append(f"Year: {year}")
            if source:
                details.append(f"Source: {source}")
            if journal:
                details.append(f"Journal: {journal}")
            if evidence:
                details.append(f"Evidence: {evidence}")
            if details:
                print(f"  {'':>12} {' | '.join(details)}")
            print()

        return 0

    except ImportError as e:
        print(f"  Warning: HybridSearch unavailable ({e})")
        print("  Falling back to simple keyword matching...")
        print()

        # Simple fallback: keyword matching
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
            p = papers[idx]
            title = p.get("title", "Unknown")
            print(f"  {rank}. [{score:.2f}] {title}")
        print()

        return 0

    except Exception as e:
        print(f"  Error during search: {e}")
        return 1
