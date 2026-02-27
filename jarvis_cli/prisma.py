"""jarvis prisma - generate PRISMA 2020 flow diagram (P2-3)."""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path


def run_prisma(args):
    """Generate PRISMA 2020 flow diagram from search logs."""
    input_files = args.files
    output_path = args.output

    # Collect stats from each search JSON
    searches = []
    all_papers = []

    for fpath in input_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            papers = data if isinstance(data, list) else data.get("papers", [])
            # Extract query from filename
            stem = Path(fpath).stem
            searches.append({
                "file": stem,
                "count": len(papers),
            })
            all_papers.extend(papers)
        except Exception as e:
            print(f"  [WARN] Error loading {fpath}: {e}")

    if not searches:
        print("Error: No valid JSON files found.", file=sys.stderr)
        return 1

    # Calculate PRISMA stats
    total_identified = sum(s["count"] for s in searches)
    n_databases = len(searches)

    # Deduplicate to count removals
    seen_pmid = set()
    seen_doi = set()
    seen_title = set()
    unique_papers = []

    for p in all_papers:
        pmid = p.get("pmid", "")
        doi = p.get("doi", "")
        title = p.get("title", "").lower().strip().rstrip(".")

        is_dup = False
        if pmid and pmid in seen_pmid:
            is_dup = True
        if doi and doi in seen_doi:
            is_dup = True
        if title and title in seen_title:
            is_dup = True

        if not is_dup:
            if pmid:
                seen_pmid.add(pmid)
            if doi:
                seen_doi.add(doi)
            if title:
                seen_title.add(title)
            unique_papers.append(p)

    n_duplicates = total_identified - len(unique_papers)

    # Screening: papers with abstract
    screened = [p for p in unique_papers if p.get("abstract")]
    n_no_abstract = len(unique_papers) - len(screened)

    # Eligibility: papers with summary (LLM processed)
    eligible = [p for p in screened if p.get("summary_ja") and not p["summary_ja"].startswith("（")]
    n_no_summary = len(screened) - len(eligible)

    # Final included
    n_included = len(eligible)

    # Build search detail string
    search_details = "\\n".join(
        f"{s['file']}: {s['count']} papers" for s in searches
    )

    # Generate Mermaid diagram
    mermaid = _build_mermaid(
        n_databases=n_databases,
        search_details=search_details,
        total_identified=total_identified,
        n_duplicates=n_duplicates,
        n_after_dedup=len(unique_papers),
        n_screened=len(unique_papers),
        n_no_abstract=n_no_abstract,
        n_after_screen=len(screened),
        n_no_summary=n_no_summary,
        n_included=n_included,
    )

    # Build markdown report
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = _build_report(now, searches, mermaid,
                       total_identified, n_duplicates,
                       len(unique_papers), n_no_abstract,
                       len(screened), n_no_summary, n_included)

    # Save
    if not output_path:
        os.makedirs("logs/prisma", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"logs/prisma/prisma_{timestamp}.md"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(md, encoding="utf-8")

    # Also save mermaid-only file for easy embedding
    mermaid_path = Path(output_path).with_suffix(".mmd")
    mermaid_path.write_text(mermaid, encoding="utf-8")

    print(f"PRISMA diagram saved to: {output_path}")
    print(f"Mermaid file saved to: {mermaid_path}")
    print()
    print(f"  Identified:  {total_identified} (from {n_databases} searches)")
    print(f"  Duplicates:  {n_duplicates}")
    print(f"  After dedup: {len(unique_papers)}")
    print(f"  No abstract: {n_no_abstract}")
    print(f"  After screen:{len(screened)}")
    print(f"  No summary:  {n_no_summary}")
    print(f"  Included:    {n_included}")

    return 0


def _build_mermaid(n_databases, search_details, total_identified,
                   n_duplicates, n_after_dedup, n_screened,
                   n_no_abstract, n_after_screen, n_no_summary,
                   n_included):
    """Build PRISMA 2020 Mermaid flowchart."""
    return f"""graph TD
    A["<b>Identification</b><br/>{n_databases} database searches<br/>Records identified<br/>(n = {total_identified})"] --> B["Duplicate removal<br/>(n = {n_duplicates} removed)"]
    B --> C["<b>Screening</b><br/>Records after dedup<br/>(n = {n_after_dedup})"]
    C --> D{{"Abstract available?"}}
    D -->|Yes| E["Records screened<br/>(n = {n_after_screen})"]
    D -->|No| F["Excluded: no abstract<br/>(n = {n_no_abstract})"]
    E --> G{{"LLM summary generated?"}}
    G -->|Yes| H["<b>Included</b><br/>Studies with summary<br/>(n = {n_included})"]
    G -->|No| I["Excluded: no summary<br/>(n = {n_no_summary})"]

    style A fill:#4CAF50,color:#fff,stroke:#333
    style C fill:#2196F3,color:#fff,stroke:#333
    style H fill:#FF9800,color:#fff,stroke:#333
    style F fill:#f44336,color:#fff,stroke:#333
    style I fill:#f44336,color:#fff,stroke:#333
"""


def _build_report(now, searches, mermaid, total_identified,
                  n_duplicates, n_after_dedup, n_no_abstract,
                  n_after_screen, n_no_summary, n_included):
    """Build PRISMA markdown report."""
    lines = [
        "# PRISMA 2020 Flow Diagram",
        "",
        f"**Generated:** {now}",
        f"**Generated by:** JARVIS Research OS",
        "",
        "---",
        "",
        "## Flow Diagram",
        "",
        "```mermaid",
        mermaid,
        "```",
        "",
        "---",
        "",
        "## Search Details",
        "",
        "| Search | Papers Found |",
        "|---|---|",
    ]

    for s in searches:
        lines.append(f"| {s['file']} | {s['count']} |")

    lines.extend([
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
        f"| Stage | Count |",
        f"|---|---|",
        f"| Identified (total) | {total_identified} |",
        f"| Duplicates removed | {n_duplicates} |",
        f"| After deduplication | {n_after_dedup} |",
        f"| Excluded (no abstract) | {n_no_abstract} |",
        f"| After screening | {n_after_screen} |",
        f"| Excluded (no summary) | {n_no_summary} |",
        f"| **Included** | **{n_included}** |",
        "",
        "---",
        "",
        f"*Generated by JARVIS Research OS on {now}*",
    ])

    return "\n".join(lines)
