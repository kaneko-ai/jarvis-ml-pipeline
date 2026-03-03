"""jarvis citation - citation analysis for collected papers (P2-2)."""

from __future__ import annotations

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path


SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper"
REQUEST_DELAY = 3.5  # seconds between requests to avoid 429


def run_citation(args):
    """Analyze citations for papers in a merged JSON file."""
    input_path = args.input
    output_path = args.output

    # Load papers
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            papers = json.load(f)
    except Exception as e:
        print(f"Error loading {input_path}: {e}", file=sys.stderr)
        return 1

    if not papers:
        print("No papers found in input file.", file=sys.stderr)
        return 1

    print(f"Loaded {len(papers)} papers from {input_path}")
    print(f"Fetching citation data from Semantic Scholar...")
    print(f"(~{len(papers) * REQUEST_DELAY / 60:.1f} minutes estimated)")
    print()

    # Fetch citation data for each paper
    success = 0
    failed = 0
    for i, paper in enumerate(papers, 1):
        doi = paper.get("doi", "")
        pmid = paper.get("pmid", "")
        title = paper.get("title", "Untitled")

        short_title = title[:50] + "..." if len(title) > 50 else title
        print(f"  [{i}/{len(papers)}] {short_title}", end="")

        citation_data = _fetch_citation_data(doi, pmid)

        if citation_data:
            paper["citation_count"] = citation_data.get("citationCount", 0)
            paper["influential_citation_count"] = citation_data.get("influentialCitationCount", 0)
            paper["semantic_scholar_id"] = citation_data.get("paperId", "")

            # Top citing papers (safely handle None)
            citations = citation_data.get("citations") or []
            paper["top_citing_papers"] = [
                {
                    "title": c.get("title", ""),
                    "year": c.get("year"),
                    "citation_count": c.get("citationCount", 0),
                }
                for c in citations[:5] if c and c.get("title")
            ]

            # Top referenced papers (safely handle None)
            references = citation_data.get("references") or []
            paper["top_references"] = [
                {
                    "title": r.get("title", ""),
                    "year": r.get("year"),
                    "citation_count": r.get("citationCount", 0),
                }
                for r in references[:5] if r and r.get("title")
            ]

            print(f" -> {paper['citation_count']} citations")
            success += 1
        else:
            paper["citation_count"] = None
            paper["influential_citation_count"] = None
            print(f" -> not found")
            failed += 1

        # Rate limiting
        if i < len(papers):
            time.sleep(REQUEST_DELAY)

    print()
    print(f"Success: {success}, Failed: {failed}")

    # Sort by citation count for ranking
    ranked = sorted(
        [p for p in papers if p.get("citation_count") is not None],
        key=lambda p: p["citation_count"],
        reverse=True,
    )

    # Save enriched JSON
    if not output_path:
        os.makedirs("logs/citation", exist_ok=True)
        safe = Path(input_path).stem
        output_path = f"logs/citation/{safe}_cited.json"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)

    # Save markdown report
    md_path = Path(output_path).with_suffix(".md")
    md = _build_citation_report(ranked, papers, success, failed)
    md_path.write_text(md, encoding="utf-8")

    print(f"Citation data saved to: {output_path}")
    print(f"Citation report saved to: {md_path}")

    # Show top 10
    print()
    print("=== Top 10 Most Cited Papers ===")
    for i, p in enumerate(ranked[:10], 1):
        title = p.get("title", "Untitled")[:60]
        count = p.get("citation_count", 0)
        year = p.get("year", "n.d.")
        print(f"  {i}. [{count} citations] ({year}) {title}")

    return 0


def _fetch_citation_data(doi, pmid):
    """Fetch citation data from Semantic Scholar API."""
    fields = "title,citationCount,influentialCitationCount,citations.title,citations.year,citations.citationCount,references.title,references.year,references.citationCount"

    # Try DOI first
    if doi:
        try:
            url = f"{SEMANTIC_SCHOLAR_API}/DOI:{doi}?fields={fields}"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                time.sleep(10)
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass

    # Fallback to PMID
    if pmid:
        try:
            url = f"{SEMANTIC_SCHOLAR_API}/PMID:{pmid}?fields={fields}"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                time.sleep(10)
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass

    return None


def _build_citation_report(ranked, all_papers, success, failed):
    """Build a citation analysis markdown report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Stats
    citation_counts = [p["citation_count"] for p in ranked]
    total_citations = sum(citation_counts) if citation_counts else 0
    avg_citations = total_citations / len(citation_counts) if citation_counts else 0
    max_citations = max(citation_counts) if citation_counts else 0
    median_idx = len(citation_counts) // 2
    median_citations = citation_counts[median_idx] if citation_counts else 0

    lines = [
        "# Citation Analysis Report",
        "",
        f"**Generated:** {now}",
        f"**Total papers:** {len(all_papers)}",
        f"**Citation data found:** {success}",
        f"**Not found:** {failed}",
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total citations (sum) | {total_citations:,} |",
        f"| Average citations | {avg_citations:.1f} |",
        f"| Median citations | {median_citations} |",
        f"| Max citations | {max_citations:,} |",
        f"| Papers with 100+ citations | {sum(1 for c in citation_counts if c >= 100)} |",
        f"| Papers with 50+ citations | {sum(1 for c in citation_counts if c >= 50)} |",
        f"| Papers with 10+ citations | {sum(1 for c in citation_counts if c >= 10)} |",
        "",
        "---",
        "",
        "## Top 20 Most Cited Papers",
        "",
        "| Rank | Citations | Year | Title |",
        "|---|---|---|---|",
    ]

    for i, p in enumerate(ranked[:20], 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "n.d.")
        count = p.get("citation_count", 0)
        doi = p.get("doi", "")
        link = f"[{title}](https://doi.org/{doi})" if doi else title
        lines.append(f"| {i} | {count:,} | {year} | {link} |")

    lines.extend([
        "",
        "---",
        "",
        "## Citation Distribution",
        "",
        "| Range | Count |",
        "|---|---|",
        f"| 500+ | {sum(1 for c in citation_counts if c >= 500)} |",
        f"| 200-499 | {sum(1 for c in citation_counts if 200 <= c < 500)} |",
        f"| 100-199 | {sum(1 for c in citation_counts if 100 <= c < 200)} |",
        f"| 50-99 | {sum(1 for c in citation_counts if 50 <= c < 100)} |",
        f"| 10-49 | {sum(1 for c in citation_counts if 10 <= c < 50)} |",
        f"| 1-9 | {sum(1 for c in citation_counts if 1 <= c < 10)} |",
        f"| 0 | {sum(1 for c in citation_counts if c == 0)} |",
        "",
        "---",
        "",
        f"*Generated by JARVIS Research OS on {now}*",
    ])

    return "\n".join(lines)
