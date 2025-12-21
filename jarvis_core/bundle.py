"""Evidence Bundle Export for audit and external tool integration.

This module provides:
- export_evidence_bundle(): Export result + evidence to local files

Per RP12, this enables "submittable evidence-based artifacts"
for research documentation.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .evidence import EvidenceStore
    from .result import EvidenceQAResult


def _safe_filename(s: str, max_length: int = 50) -> str:
    """Convert string to safe filename."""
    # Replace unsafe characters
    safe = re.sub(r"[<>:\"/\\|?*]", "_", s)
    # Limit length
    if len(safe) > max_length:
        safe = safe[:max_length]
    return safe


def export_evidence_bundle(
    result: "EvidenceQAResult",
    store: "EvidenceStore",
    out_dir: str,
    ref_style: str = "vancouver",
) -> str:
    """Export Evidence QA result as a bundle.

    Creates a directory with:
    - bundle.json: Structured result
    - evidence/: Directory with chunk texts
    - citations.md: Human-readable citation list
    - references.md: Academic reference list (Vancouver/APA)

    Args:
        result: The EvidenceQAResult to export.
        store: EvidenceStore containing chunk data.
        out_dir: Output directory path.
        ref_style: Reference style ("vancouver" or "apa").

    Returns:
        Path to the created bundle directory.
    """
    from .reference import extract_references
    from .reference_formatter import format_references_markdown

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Extract references from citations
    refs = extract_references(result.citations, store)

    # 1. Export bundle.json (with references)
    bundle_data = result.to_dict()
    bundle_data["references"] = [r.to_dict() for r in refs]
    bundle_path = out_path / "bundle.json"
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle_data, f, indent=2, ensure_ascii=False)

    # 2. Export evidence chunks
    evidence_dir = out_path / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    for chunk_id in result.chunks_used:
        chunk = store.get_chunk(chunk_id)
        if chunk:
            # Use chunk_id as filename (already UUID, safe)
            chunk_path = evidence_dir / f"{_safe_filename(chunk_id)}.txt"
            content = f"# Chunk: {chunk_id}\n"
            content += f"Source: {chunk.source}\n"
            content += f"Locator: {chunk.locator}\n"
            content += f"\n---\n\n{chunk.text}"
            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(content)

    # 3. Export citations.md
    citations_md = _generate_citations_md(result, store)
    citations_path = out_path / "citations.md"
    with open(citations_path, "w", encoding="utf-8") as f:
        f.write(citations_md)

    # 4. Export references.md (RP14)
    style = "apa" if ref_style.lower() == "apa" else "vancouver"
    refs_md = format_references_markdown(refs, style=style)
    refs_path = out_path / "references.md"
    with open(refs_path, "w", encoding="utf-8") as f:
        f.write(refs_md)

    # 5. Export BibTeX (RP15)
    from .bibtex import export_bibtex
    bibtex_content = export_bibtex(refs)
    bibtex_path = out_path / "references.bib"
    with open(bibtex_path, "w", encoding="utf-8") as f:
        f.write(bibtex_content)

    # 6. Export RIS (RP15)
    from .ris import export_ris
    ris_content = export_ris(refs)
    ris_path = out_path / "references.ris"
    with open(ris_path, "w", encoding="utf-8") as f:
        f.write(ris_content)

    # 7. Export Claims (RP16)
    if result.claims is not None:
        from .claim_export import (
            export_claims_markdown,
            export_claims_json,
            export_claims_pptx_outline,
        )

        # claims.md
        claims_md = export_claims_markdown(result.claims, refs)
        claims_md_path = out_path / "claims.md"
        with open(claims_md_path, "w", encoding="utf-8") as f:
            f.write(claims_md)

        # claims.json
        claims_json = export_claims_json(result.claims, refs)
        claims_json_path = out_path / "claims.json"
        with open(claims_json_path, "w", encoding="utf-8") as f:
            f.write(claims_json)

        # slides_outline.txt
        slides_outline = export_claims_pptx_outline(
            result.claims, refs, title=result.query
        )
        slides_path = out_path / "slides_outline.txt"
        with open(slides_path, "w", encoding="utf-8") as f:
            f.write(slides_outline)

    # 8. Knowledge Tool Integrations (RP19)
    from .integrations.notebooklm import export_notebooklm
    from .integrations.obsidian import export_obsidian
    from .integrations.notion import export_notion

    # NotebookLM (single markdown file)
    notebooklm_content = export_notebooklm(result, refs, store)
    notebooklm_path = out_path / "notebooklm.md"
    with open(notebooklm_path, "w", encoding="utf-8") as f:
        f.write(notebooklm_content)

    # Obsidian (vault structure)
    obsidian_dir = out_path / "obsidian"
    export_obsidian(result, refs, str(obsidian_dir))

    # Notion (JSON export)
    notion_content = export_notion(result, refs)
    notion_path = out_path / "notion.json"
    with open(notion_path, "w", encoding="utf-8") as f:
        f.write(notion_content)

    return str(out_path)


def _generate_citations_md(
    result: "EvidenceQAResult",
    store: "EvidenceStore",
) -> str:
    """Generate human-readable citations markdown."""
    lines = [
        "# Citations",
        "",
        f"**Query:** {result.query}",
        "",
        f"**Status:** {result.status}",
        "",
        "---",
        "",
        "## Answer",
        "",
        result.answer,
        "",
        "---",
        "",
    ]

    # Add claims section if present (RP13)
    if result.claims is not None and hasattr(result.claims, "claims"):
        lines.append("## Claims")
        lines.append("")

        for i, claim in enumerate(result.claims.claims, 1):
            status_mark = "✓" if claim.valid else "✗"
            lines.append(f"### {status_mark} Claim {i}")
            lines.append("")
            lines.append(f"**Text:** {claim.text}")
            lines.append("")
            lines.append(f"**Citations:** {', '.join(claim.citations) or '(none)'}")
            lines.append("")
            if not claim.valid and claim.validation_notes:
                lines.append(f"**Notes:** {', '.join(claim.validation_notes)}")
                lines.append("")
            lines.append("---")
            lines.append("")

    # Evidence section
    lines.append("## Evidence Used")
    lines.append("")

    for i, citation in enumerate(result.citations, 1):
        chunk = store.get_chunk(citation.chunk_id)
        quote = citation.quote if citation.quote else "(quote not available)"

        lines.append(f"### [{i}] {citation.locator}")
        lines.append("")
        lines.append(f"**Chunk ID:** `{citation.chunk_id}`")
        lines.append("")
        lines.append(f"**Source:** {citation.source}")
        lines.append("")
        lines.append(f"**Quote:** {quote}")
        lines.append("")
        if chunk:
            # Show first 200 chars of full text
            preview = chunk.text[:200]
            if len(chunk.text) > 200:
                preview += "..."
            lines.append(f"**Context:** {preview}")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Inputs")
    lines.append("")
    for inp in result.inputs:
        lines.append(f"- {inp}")
    lines.append("")

    lines.append("## Metadata")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(result.meta, indent=2, ensure_ascii=False))
    lines.append("```")

    return "\n".join(lines)
