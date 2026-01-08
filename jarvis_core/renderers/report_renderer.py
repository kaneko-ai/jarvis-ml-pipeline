"""Report Renderer.

Per RP-123, generates research-ready Markdown reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReportSection:
    """A section in the report."""

    title: str
    content: str
    level: int = 2


def render_claimset_report(
    query: str,
    claims: list[dict],
    evidence: dict[str, dict],
    metadata: dict | None = None,
) -> str:
    """Render a ClaimSet as a research report.

    Args:
        query: Original research query.
        claims: List of claim dicts with text, citations, type.
        evidence: Map of chunk_id -> evidence details.
        metadata: Optional run metadata.

    Returns:
        Markdown report string.
    """
    lines = []

    # Header
    lines.append("# Research Summary")
    lines.append("")
    lines.append(f"**Query:** {query}")
    if metadata:
        lines.append(f"**Run ID:** {metadata.get('run_id', 'N/A')}")
        lines.append(f"**Generated:** {metadata.get('timestamp', datetime.now().isoformat())}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    fact_count = sum(1 for c in claims if c.get("type") == "fact")
    interp_count = sum(1 for c in claims if c.get("type") == "interpretation")
    lines.append(f"- **Total Claims:** {len(claims)}")
    lines.append(f"- **Facts:** {fact_count}")
    lines.append(f"- **Interpretations:** {interp_count}")
    lines.append(f"- **Evidence Chunks:** {len(evidence)}")
    lines.append("")

    # Key Findings (Facts)
    facts = [c for c in claims if c.get("type") == "fact"]
    if facts:
        lines.append("## Key Findings")
        lines.append("")
        for i, claim in enumerate(facts[:10], 1):
            lines.append(f"### {i}. {claim.get('text', '')[:100]}...")
            lines.append("")

            # Evidence
            citations = claim.get("citations", [])
            if citations:
                lines.append("**Evidence:**")
                for cid in citations[:3]:
                    ev = evidence.get(cid, {})
                    quote = ev.get("quote", "")[:150]
                    locator = ev.get("locator", cid)
                    lines.append(f'- `{locator}`: "{quote}..."')
                lines.append("")

    # Interpretations
    interpretations = [c for c in claims if c.get("type") == "interpretation"]
    if interpretations:
        lines.append("## Interpretations & Hypotheses")
        lines.append("")
        for i, claim in enumerate(interpretations[:5], 1):
            lines.append(f"{i}. {claim.get('text', '')}")
        lines.append("")

    # Gaps
    gaps = [c for c in claims if not c.get("citations")]
    if gaps:
        lines.append("## ⚠️ Gaps (Unsupported Claims)")
        lines.append("")
        for claim in gaps[:5]:
            lines.append(f"- {claim.get('text', '')[:100]}...")
        lines.append("")

    # References
    lines.append("## References")
    lines.append("")
    seen_sources = set()
    for ev in evidence.values():
        source = ev.get("source", "")
        if source and source not in seen_sources:
            seen_sources.add(source)
            lines.append(f"- {source}")
    lines.append("")

    return "\n".join(lines)


def render_comparison_report(
    query: str,
    papers: list[dict],
    comparison_matrix: dict[str, dict[str, str]],
) -> str:
    """Render a paper comparison report.

    Args:
        query: Research query.
        papers: List of paper metadata dicts.
        comparison_matrix: Matrix of paper_id -> aspect -> value.

    Returns:
        Markdown comparison report.
    """
    lines = []

    lines.append("# Paper Comparison")
    lines.append("")
    lines.append(f"**Query:** {query}")
    lines.append(f"**Papers Compared:** {len(papers)}")
    lines.append("")

    # Comparison table
    if papers and comparison_matrix:
        # Get all aspects
        aspects = set()
        for paper_aspects in comparison_matrix.values():
            aspects.update(paper_aspects.keys())
        aspects = sorted(aspects)

        # Header row
        header = "| Paper | " + " | ".join(aspects) + " |"
        separator = "|" + "|".join(["---"] * (len(aspects) + 1)) + "|"

        lines.append(header)
        lines.append(separator)

        for paper in papers[:10]:
            paper_id = paper.get("paper_id", "")
            title = paper.get("title", "")[:30]
            row_values = [comparison_matrix.get(paper_id, {}).get(a, "-") for a in aspects]
            row = f"| {title} | " + " | ".join(row_values) + " |"
            lines.append(row)

        lines.append("")

    return "\n".join(lines)
