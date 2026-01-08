"""Obsidian exporter for Evidence Bundle.

Obsidian is a knowledge graph with bidirectional links.
Each Claim becomes a note, linked to sources and the query.

Per RP19, this creates a vault structure optimized for knowledge building.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..reference import Reference
    from ..result import EvidenceQAResult


def _safe_filename(s: str, max_length: int = 40) -> str:
    """Convert string to safe filename for Obsidian notes."""
    # Replace special characters
    safe = re.sub(r"[<>:\"/\\|?*\[\]]", "_", s)
    # Limit length
    if len(safe) > max_length:
        safe = safe[:max_length]
    return safe.strip()


def _to_wikilink(text: str) -> str:
    """Convert text to Obsidian wikilink format."""
    return f"[[{_safe_filename(text)}]]"


def export_obsidian(
    result: EvidenceQAResult,
    references: list[Reference],
    out_dir: str,
) -> str:
    """Export Evidence Bundle as Obsidian vault structure.

    Creates:
    - notes/Claim_*.md - One note per claim
    - sources/*.md - One note per source
    - index.md - Main entry point

    Args:
        result: The EvidenceQAResult.
        references: List of extracted references.
        out_dir: Output directory for obsidian vault.

    Returns:
        Path to the created obsidian directory.
    """
    out_path = Path(out_dir)
    notes_dir = out_path / "notes"
    sources_dir = out_path / "sources"

    notes_dir.mkdir(parents=True, exist_ok=True)
    sources_dir.mkdir(parents=True, exist_ok=True)

    query_safe = _safe_filename(result.query[:30])
    query_filename = f"Query_{query_safe}"

    # Create source notes
    source_files: dict[str, str] = {}
    for ref in references:
        source_name = _safe_filename(ref.get_display_locator())
        source_files[ref.id] = source_name

        source_content = _generate_source_note(ref, result)
        source_path = sources_dir / f"{source_name}.md"
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_content)

    # Create claim notes
    claim_files: dict[str, str] = {}
    if result.claims is not None:
        for i, claim in enumerate(result.claims.claims, 1):
            claim_name = f"Claim_{i}_{claim.id[:8]}"
            claim_files[claim.id] = claim_name

            claim_content = _generate_claim_note(
                claim, i, references, source_files, query_filename
            )
            claim_path = notes_dir / f"{claim_name}.md"
            with open(claim_path, "w", encoding="utf-8") as f:
                f.write(claim_content)

    # Create query (index) note
    index_content = _generate_query_note(
        result, references, claim_files, source_files
    )
    index_path = out_path / f"{query_filename}.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    # Create main index
    main_index = _generate_main_index(result, query_filename)
    main_index_path = out_path / "index.md"
    with open(main_index_path, "w", encoding="utf-8") as f:
        f.write(main_index)

    return str(out_path)


def _generate_claim_note(
    claim,
    index: int,
    references: list[Reference],
    source_files: dict[str, str],
    query_filename: str,
) -> str:
    """Generate a claim note with bidirectional links."""
    lines = [
        f"# Claim {index}",
        "",
        claim.text,
        "",
        "---",
        "",
        "## Evidence",
        "",
    ]

    # Find sources for this claim
    for ref in references:
        if any(cid in claim.citations for cid in ref.chunk_ids):
            source_link = f"[[{source_files[ref.id]}]]"
            pages = ref.get_pages_display()
            if pages:
                lines.append(f"- {source_link} ({pages})")
            else:
                lines.append(f"- {source_link}")

    lines.extend([
        "",
        "---",
        "",
        "## Used in",
        "",
        f"- [[{query_filename}]]",
        "",
        "---",
        "",
        f"Status: {'✓ Valid' if claim.valid else '? Unverified'}",
    ])

    return "\n".join(lines)


def _generate_source_note(ref: Reference, result: EvidenceQAResult) -> str:
    """Generate a source note."""
    lines = [
        f"# {ref.get_display_locator()}",
        "",
        f"**Type:** {ref.source_type.upper()}",
        "",
    ]

    if ref.year:
        lines.append(f"**Year:** {ref.year}")
        lines.append("")

    if ref.authors:
        lines.append(f"**Authors:** {', '.join(ref.authors)}")
        lines.append("")

    if ref.get_pages_display():
        lines.append(f"**Pages cited:** {ref.get_pages_display()}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Locator",
        "",
        f"`{ref.locator}`",
        "",
        "---",
        "",
        "## Referenced by",
        "",
    ])

    # Find claims that use this source
    if result.claims is not None:
        for i, claim in enumerate(result.claims.claims, 1):
            if any(cid in ref.chunk_ids for cid in claim.citations):
                lines.append(f"- [[Claim_{i}_{claim.id[:8]}]]")

    return "\n".join(lines)


def _generate_query_note(
    result: EvidenceQAResult,
    references: list[Reference],
    claim_files: dict[str, str],
    source_files: dict[str, str],
) -> str:
    """Generate the main query note."""
    lines = [
        f"# {result.query}",
        "",
        "---",
        "",
        "## Answer",
        "",
        result.answer,
        "",
        "---",
        "",
        "## Claims",
        "",
    ]

    if result.claims is not None:
        for i, claim in enumerate(result.claims.claims, 1):
            claim_link = f"[[{claim_files.get(claim.id, f'Claim_{i}')}]]"
            status = "✓" if claim.valid else "?"
            lines.append(f"- {status} {claim_link}: {claim.text[:50]}...")

    lines.extend([
        "",
        "---",
        "",
        "## Sources",
        "",
    ])

    for ref in references:
        source_link = f"[[{source_files[ref.id]}]]"
        lines.append(f"- {source_link}")

    lines.extend([
        "",
        "---",
        "",
        f"*Status: {result.status}*",
    ])

    return "\n".join(lines)


def _generate_main_index(result: EvidenceQAResult, query_filename: str) -> str:
    """Generate the main index file."""
    lines = [
        "# Research Vault",
        "",
        "## Queries",
        "",
        f"- [[{query_filename}]]",
        "",
        "---",
        "",
        "*Generated by Jarvis Evidence QA*",
    ]
    return "\n".join(lines)
