#!/usr/bin/env python
"""Build Frozen Evaluation Set.

Per RP-34, generates frozen JSONL from PMID list.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_frozen_entry(pmid: str, query: str, category: str = "paper_survey") -> dict:
    """Build a frozen evaluation entry."""
    return {
        "task_id": f"frozen_{pmid}",
        "category": category,
        "query": query,
        "expected_entities": [],  # TODO: populate from abstract
        "min_citations": 2,
        "pmid_seed": pmid,
        "notes": "Auto-generated - needs manual review",
    }


def main():
    parser = argparse.ArgumentParser(description="Build frozen evaluation set")
    parser.add_argument("--pmids", type=str, help="Comma-separated PMIDs")
    parser.add_argument("--pmid-file", type=str, help="File with one PMID per line")
    parser.add_argument("--query-template", type=str, default="{title}", help="Query template")
    parser.add_argument("--out", type=str, default="docs/evals/frozen_candidates.jsonl")

    args = parser.parse_args()

    pmids = []

    if args.pmids:
        pmids = [p.strip() for p in args.pmids.split(",")]
    elif args.pmid_file:
        with open(args.pmid_file, "r") as f:
            pmids = [line.strip() for line in f if line.strip()]
    else:
        print("Provide --pmids or --pmid-file", file=sys.stderr)
        sys.exit(1)

    # Fetch metadata if available
    try:
        from jarvis_tools.papers import pubmed_esummary

        papers = pubmed_esummary(pmids)
        paper_map = {p.pmid: p for p in papers}
    except Exception:
        paper_map = {}

    # Generate entries
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        for pmid in pmids:
            paper = paper_map.get(pmid)
            if paper:
                query = args.query_template.format(title=paper.title[:50])
            else:
                query = f"PMID:{pmid}"

            entry = build_frozen_entry(pmid, query)
            if paper:
                entry["notes"] = f"Title: {paper.title[:80]}"

            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Generated {len(pmids)} entries to {args.out}")


if __name__ == "__main__":
    main()
