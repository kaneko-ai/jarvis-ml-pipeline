"""
Merge multiple search result JSONs, deduplicate by PMID/DOI/title.
Usage:
    python -m jarvis_cli merge logs/search/*.json
    python -m jarvis_cli merge logs/search/*.json --output merged.json --bibtex
"""
import json
import os
import glob
import argparse
from pathlib import Path
from datetime import datetime


def normalize_title(title: str) -> str:
    """Normalize title for deduplication."""
    return title.lower().strip().rstrip(".")


def merge_papers(json_files: list[str]) -> list[dict]:
    """Load papers from multiple JSON files and deduplicate."""
    all_papers = []
    for fpath in json_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_papers.extend(data)
                elif isinstance(data, dict) and "papers" in data:
                    all_papers.extend(data["papers"])
                else:
                    print(f"  [WARN] Skipping {fpath}: unexpected format")
        except Exception as e:
            print(f"  [WARN] Error loading {fpath}: {e}")

    # Deduplicate
    seen_pmid = set()
    seen_doi = set()
    seen_title = set()
    unique = []

    for paper in all_papers:
        pmid = paper.get("pmid", "")
        doi = paper.get("doi", "")
        title = normalize_title(paper.get("title", ""))

        # Skip if we've seen this paper before
        if pmid and pmid in seen_pmid:
            continue
        if doi and doi in seen_doi:
            continue
        if title and title in seen_title:
            continue

        if pmid:
            seen_pmid.add(pmid)
        if doi:
            seen_doi.add(doi)
        if title:
            seen_title.add(title)
        unique.append(paper)

    return unique


def save_merged(papers: list[dict], output_path: str):
    """Save merged papers to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"  Saved {len(papers)} papers to {output_path}")


def run_merge(args):
    """Main merge function."""
    # Expand glob patterns (PowerShell 5.1 may not expand them)
    json_files = []
    for pattern in args.files:
        expanded = glob.glob(pattern)
        if expanded:
            json_files.extend(expanded)
        else:
            # Try as literal filename
            if os.path.exists(pattern):
                json_files.append(pattern)
            else:
                print(f"  [WARN] No files matching: {pattern}")

    if not json_files:
        print("  [ERROR] No JSON files found.")
        return

    print(f"  Loading {len(json_files)} files...")
    for f in json_files:
        print(f"    - {f}")

    papers = merge_papers(json_files)
    print(f"  Found {len(papers)} unique papers (after deduplication)")

    # Output path
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"logs/search/merged_{timestamp}.json"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_merged(papers, output_path)

    # Optional BibTeX
    if args.bibtex:
        from jarvis_cli.bibtex import papers_to_bibtex
        bib_path = output_path.replace(".json", ".bib")
        bib_content = papers_to_bibtex(papers)
        with open(bib_path, "w", encoding="utf-8") as f:
            f.write(bib_content)
        print(f"  Saved BibTeX to {bib_path}")

    # Summary
    print(f"\n  --- Merge Summary ---")
    print(f"  Input files:    {len(json_files)}")
    print(f"  Total papers:   {sum(1 for _ in json_files)}")
    print(f"  Unique papers:  {len(papers)}")
    print(f"  Output:         {output_path}")

    return papers
