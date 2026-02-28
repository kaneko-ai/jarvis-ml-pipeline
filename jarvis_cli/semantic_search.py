"""jarvis semantic-search - Semantic search within collected papers (v2 T3-1).

Uses HybridSearch (Sentence Transformers + BM25 with RRF fusion) to find
the most relevant papers in a local collection by meaning, not just keywords.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def run_semantic_search(args):
    """semantic-search command main logic."""
    from jarvis_core.embeddings.hybrid import HybridSearch

    query = args.query.strip()
    db_path = Path(args.db)
    top_n = getattr(args, "top", 10)

    if not query:
        print("Error: search query is empty.", file=sys.stderr)
        return 1

    if not db_path.exists():
        print(f"Error: File not found: {db_path}", file=sys.stderr)
        return 1

    # 1. Load papers
    try:
        papers = json.loads(db_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(papers, list) or len(papers) == 0:
        print("Error: JSON must be a non-empty array of papers.", file=sys.stderr)
        return 1

    print(f"Semantic search: '{query}'")
    print(f"  Database: {db_path.name} ({len(papers)} papers)")
    print(f"  Top {top_n} results")
    print()

    # 2. Build corpus from title + abstract
    corpus = []
    valid_indices = []
    for i, p in enumerate(papers):
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        text = f"{title}. {abstract}".strip()
        if text and text != ".":
            corpus.append(text)
            valid_indices.append(i)

    if not corpus:
        print("Error: No papers with title/abstract found.", file=sys.stderr)
        return 1

    print(f"  Building index for {len(corpus)} papers (first run may download model ~80MB)...")

    # 3. Run hybrid search
    try:
        searcher = HybridSearch()
        searcher.index(corpus)
        results = searcher.search(query, top_k=min(top_n, len(corpus)))
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        return 1

    # 4. Display results
    print()
    print(f"  Top {len(results)} results:")
    print("=" * 60)

    for rank, (idx, score) in enumerate(results, 1):
        if idx < len(valid_indices):
            paper_idx = valid_indices[idx]
            paper = papers[paper_idx]
        else:
            continue

        title = paper.get("title", "Untitled")
        year = paper.get("year", "n.d.")
        source = paper.get("source", "?")
        journal = paper.get("journal", paper.get("venue", ""))
        evidence = paper.get("evidence_level", "")

        print(f"  [{rank}] (score: {score:.4f}) {title}")
        print(f"      Year: {year} | Source: {source}", end="")
        if journal:
            print(f" | Journal: {journal}", end="")
        if evidence and evidence != "unknown":
            print(f" | Evidence: {evidence}", end="")
        print()
        print()

    print("=" * 60)
    return 0
