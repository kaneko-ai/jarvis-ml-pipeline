"""Claim export for reuse in presentations and documents.

This module provides:
- export_claims(): Export ClaimSet to various formats

Per RP16, this enables "research → presentation" in one pipeline.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .claim import ClaimSet
    from .reference import Reference


def _get_source_display(locator: str) -> str:
    """Get human-readable source display from locator."""
    if locator.startswith("pdf:"):
        # Extract filename
        import re
        match = re.search(r"pdf:(.+?)(?:#|$)", locator)
        if match:
            return f"PDF: {match.group(1)}"
    elif locator.startswith("url:"):
        match = re.search(r"url:(.+?)(?:#|$)", locator)
        if match:
            return f"URL: {match.group(1)}"
    return locator


def export_claims_markdown(
    claims: ClaimSet,
    references: list[Reference] | None = None,
) -> str:
    """Export ClaimSet to Markdown format.

    Each claim becomes a section with its supporting sources.

    Args:
        claims: The ClaimSet to export.
        references: Optional list of references for source mapping.

    Returns:
        Markdown formatted claims.
    """
    lines = [
        "# Claims",
        "",
    ]

    for i, claim in enumerate(claims.claims, 1):
        status = "✓" if claim.valid else "?"
        lines.append(f"## {status} Claim {i}")
        lines.append("")
        lines.append(claim.text)
        lines.append("")

        if claim.citations:
            lines.append("**Sources:**")
            for cid in claim.citations:
                # Try to find reference
                ref_display = f"chunk: {cid[:12]}..."
                if references:
                    for ref in references:
                        if cid in ref.chunk_ids:
                            ref_display = f"{ref.id}: {ref.get_display_locator()}"
                            if ref.get_pages_display():
                                ref_display += f" ({ref.get_pages_display()})"
                            break
                lines.append(f"- {ref_display}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def export_claims_json(
    claims: ClaimSet,
    references: list[Reference] | None = None,
) -> str:
    """Export ClaimSet to JSON format.

    Args:
        claims: The ClaimSet to export.
        references: Optional list of references for reference mapping.

    Returns:
        JSON formatted claims.
    """
    # Build reference mapping
    chunk_to_ref: dict[str, str] = {}
    if references:
        for ref in references:
            for cid in ref.chunk_ids:
                chunk_to_ref[cid] = ref.id

    claims_data = []
    for claim in claims.claims:
        claim_refs = list(set(chunk_to_ref.get(cid, "") for cid in claim.citations))
        claim_refs = [r for r in claim_refs if r]  # Remove empty

        claims_data.append({
            "id": claim.id,
            "text": claim.text,
            "valid": claim.valid,
            "citations": claim.citations,
            "references": claim_refs,
        })

    output = {
        "claims": claims_data,
        "total": len(claims_data),
        "valid_count": sum(1 for c in claims.claims if c.valid),
    }

    return json.dumps(output, indent=2, ensure_ascii=False)


def export_claims_pptx_outline(
    claims: ClaimSet,
    references: list[Reference] | None = None,
    title: str = "Research Findings",
) -> str:
    """Export ClaimSet as PPTX outline (text format).

    Each claim becomes one slide. This is a text outline,
    not actual PPTX (which would require python-pptx).

    Args:
        claims: The ClaimSet to export.
        references: Optional list of references for source mapping.
        title: Title for the presentation.

    Returns:
        Text-based slide outline.
    """
    # Build reference mapping
    chunk_to_ref: dict[str, Reference] = {}
    if references:
        for ref in references:
            for cid in ref.chunk_ids:
                chunk_to_ref[cid] = ref

    lines = [
        "=" * 60,
        f"PRESENTATION OUTLINE: {title}",
        "=" * 60,
        "",
    ]

    # Title slide
    lines.append("Slide 1: Title")
    lines.append(f"  - {title}")
    lines.append("  - [Your Name]")
    lines.append("  - [Date]")
    lines.append("")

    # Claim slides
    slide_num = 2
    for claim in claims.claims:
        if not claim.valid:
            continue  # Skip invalid claims in presentation

        lines.append(f"Slide {slide_num}: {claim.text[:50]}...")
        lines.append(f"  - {claim.text}")
        lines.append("")

        # Add sources
        if claim.citations:
            sources = []
            for cid in claim.citations[:2]:  # Limit to 2 sources per slide
                if cid in chunk_to_ref:
                    ref = chunk_to_ref[cid]
                    sources.append(ref.get_display_locator())
                else:
                    sources.append(f"[{cid[:8]}]")
            lines.append(f"  Source: {', '.join(sources)}")
            lines.append("")

        slide_num += 1

    # Summary slide
    valid_claims = [c for c in claims.claims if c.valid]
    lines.append(f"Slide {slide_num}: Summary")
    lines.append("  Key Findings:")
    for i, claim in enumerate(valid_claims[:5], 1):  # Top 5
        lines.append(f"    {i}. {claim.text[:60]}...")
    lines.append("")

    # References slide
    lines.append(f"Slide {slide_num + 1}: References")
    if references:
        for ref in references[:5]:  # Top 5 refs
            lines.append(f"  - {ref.get_display_locator()}")
    lines.append("")

    lines.append("=" * 60)
    lines.append(f"Total slides: {slide_num + 1}")

    return "\n".join(lines)


def export_claims(
    claims: ClaimSet,
    format: Literal["markdown", "json", "pptx_outline"] = "markdown",
    references: list[Reference] | None = None,
    title: str = "Research Findings",
) -> str:
    """Export ClaimSet to the specified format.

    Args:
        claims: The ClaimSet to export.
        format: Output format ("markdown", "json", "pptx_outline").
        references: Optional list of references.
        title: Title for presentation outline.

    Returns:
        Formatted output string.
    """
    if format == "markdown":
        return export_claims_markdown(claims, references)
    elif format == "json":
        return export_claims_json(claims, references)
    elif format == "pptx_outline":
        return export_claims_pptx_outline(claims, references, title)
    else:
        raise ValueError(f"Unknown format: {format}")
