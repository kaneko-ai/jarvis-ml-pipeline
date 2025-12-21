"""NotebookLM exporter for Evidence Bundle.

NotebookLM works best with a single, well-structured markdown file
that it can summarize, discuss, and convert to audio.

Per RP19, this creates a document optimized for NotebookLM's understanding.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..result import EvidenceQAResult
    from ..claim import ClaimSet
    from ..reference import Reference
    from ..evidence import EvidenceStore


def export_notebooklm(
    result: "EvidenceQAResult",
    references: List["Reference"],
    store: "EvidenceStore" | None = None,
) -> str:
    """Export Evidence Bundle for NotebookLM.

    Creates a single markdown file with clear section headers
    that NotebookLM can process effectively.

    Args:
        result: The EvidenceQAResult.
        references: List of extracted references.
        store: Optional EvidenceStore for evidence text.

    Returns:
        Markdown content for NotebookLM.
    """
    lines = [
        "# Research Summary",
        "",
        "---",
        "",
        "## Query",
        "",
        result.query,
        "",
        "---",
        "",
        "## Answer (Summary)",
        "",
        result.answer,
        "",
        "---",
        "",
    ]

    # Claims section
    if result.claims is not None:
        lines.append("## Key Findings (Claims)")
        lines.append("")

        for i, claim in enumerate(result.claims.claims, 1):
            if claim.valid:
                lines.append(f"{i}. {claim.text}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Evidence section (grouped by source)
    lines.append("## Evidence")
    lines.append("")

    # Group chunks by reference
    ref_evidence: dict[str, List[str]] = {}
    for ref in references:
        ref_evidence[ref.id] = []
        if store:
            for chunk_id in ref.chunk_ids[:3]:  # Limit per source
                chunk = store.get_chunk(chunk_id)
                if chunk:
                    preview = chunk.text[:300]
                    if len(chunk.text) > 300:
                        preview += "..."
                    ref_evidence[ref.id].append(preview)

    for ref in references:
        lines.append(f"### Source: {ref.get_display_locator()}")
        if ref.get_pages_display():
            lines.append(f"*{ref.get_pages_display()}*")
        lines.append("")

        for evidence in ref_evidence.get(ref.id, []):
            lines.append(f"> {evidence}")
            lines.append("")

        lines.append("")

    lines.append("---")
    lines.append("")

    # References section
    lines.append("## References")
    lines.append("")

    for i, ref in enumerate(references, 1):
        display = ref.get_display_locator()
        if ref.year:
            display += f" ({ref.year})"
        lines.append(f"{i}. {display}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated from {len(result.citations)} citations across {len(references)} sources.*")

    return "\n".join(lines)
