"""jarvis search - lightweight paper search (P1-1 + P1-3)."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from jarvis_cli.bibtex import save_bibtex


def run_search(args):
    """search command main logic."""
    from jarvis_core.agents import PaperFetcherAgent
    from jarvis_core.llm import LLMClient

    query = args.query.strip()
    max_results = max(1, min(args.max_results, 20))

    if not query:
        print("Error: search query is empty.", file=sys.stderr)
        return 1

    print(f"Searching for: '{query}' (max {max_results} papers)...")
    print()

    agent = PaperFetcherAgent()
    start_time = time.perf_counter()
    papers, warnings = agent._search_papers(query=query, max_results=max_results)
    search_duration = time.perf_counter() - start_time

    if not papers:
        print(f"No papers found for '{query}'.")
        if warnings:
            for w in warnings:
                print(f"  Warning: {w}")
        return 1

    print(f"Found {len(papers)} papers in {search_duration:.1f}s")

    if not args.no_summary:
        print("Adding LLM summaries (may take a moment)...")
        try:
            llm = LLMClient()
            papers = agent._enrich_papers_with_llm(llm, papers)
            print("Done.")
        except Exception as e:
            print(f"Warning: LLM summary failed: {e}")
            print("Continuing without summaries.")
    print()

    if args.json_output:
        print(json.dumps(papers, ensure_ascii=False, indent=2))
    else:
        _print_papers(papers)

    output_path = _get_output_path(args.output, query, args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.json_output:
        output_path.write_text(
            json.dumps(papers, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        md = _build_report_md(query, papers, warnings, search_duration)
        output_path.write_text(md, encoding="utf-8")

    # BibTeX output (P1-3)
    if getattr(args, "bibtex", False):
        bib_path = output_path.with_suffix(".bib")
        save_bibtex(papers, bib_path)
        print(f"BibTeX saved to: {bib_path}")

    print()
    print(f"Report saved to: {output_path}")

    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")

    return 0


def _print_papers(papers):
    """Print papers to terminal."""
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "n.d.")
        source = p.get("source", "?")
        journal = p.get("journal", "")
        evidence = p.get("evidence_level", "")
        summary = p.get("summary_ja", "")

        print(f"[{i}] {title}")
        print(f"    Year: {year} | Source: {source}", end="")
        if journal:
            print(f" | Journal: {journal}", end="")
        print()
        if evidence and evidence != "N/A":
            print(f"    CEBM Level: {evidence}")
        if summary:
            print(f"    Summary: {summary}")
        print()


def _get_output_path(user_path, query, is_json):
    """Decide output file path."""
    if user_path:
        return Path(user_path)

    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in query)
    safe = safe.strip("_")[:30]
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "json" if is_json else "md"
    return Path("logs") / "search" / f"{safe}_{date_str}.{ext}"


def _build_report_md(query, papers, warnings, duration):
    """Build a Markdown report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Paper Search: {query}",
        "",
        f"**Date:** {now}",
        f"**Papers found:** {len(papers)}",
        f"**Search time:** {duration:.1f}s",
        "",
        "---",
        "",
    ]

    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "n.d.")
        authors = p.get("authors", [])
        journal = p.get("journal", "")
        source = p.get("source", "")
        doi = p.get("doi", "")
        pmid = p.get("pmid", "")
        url = p.get("url", "")
        evidence = p.get("evidence_level", "")
        summary = p.get("summary_ja", "")
        abstract = p.get("abstract", "")

        lines.append(f"## {i}. {title}")
        lines.append("")

        if authors:
            author_str = ", ".join(authors[:5])
            if len(authors) > 5:
                author_str += f" et al. ({len(authors)} authors)"
            lines.append(f"**Authors:** {author_str}")
        lines.append(f"**Year:** {year}")
        if journal:
            lines.append(f"**Journal:** {journal}")
        lines.append(f"**Source:** {source}")
        if evidence and evidence != "N/A":
            lines.append(f"**CEBM Evidence Level:** {evidence}")
        lines.append("")

        link_parts = []
        if url:
            link_parts.append(f"[Link]({url})")
        if doi:
            link_parts.append(f"[DOI](https://doi.org/{doi})")
        if pmid:
            link_parts.append(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
        if link_parts:
            lines.append(" | ".join(link_parts))
            lines.append("")

        if summary:
            lines.append("### Summary (Japanese)")
            lines.append("")
            lines.append(summary)
            lines.append("")

        if abstract:
            lines.append("<details>")
            lines.append("<summary>Abstract (English)</summary>")
            lines.append("")
            lines.append(abstract)
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append("## References")
    lines.append("")
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        authors = p.get("authors", [])
        year = p.get("year", "n.d.")
        journal = p.get("journal", "")
        doi = p.get("doi", "")
        a_str = ", ".join(authors[:3])
        if len(authors) > 3:
            a_str += " et al."
        ref = f"{i}. {a_str} ({year}). {title}. {journal}."
        if doi:
            ref += f" doi:{doi}"
        lines.append(ref)
        lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append(f"*Generated by JARVIS Research OS on {now}*")
    return "\n".join(lines)