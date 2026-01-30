"""RIS exporter for reference management tools.

This module provides:
- export_ris(): Export references to RIS format

Per RP15, this enables direct import into Zotero/EndNote.
RIS format reference: https://en.wikipedia.org/wiki/RIS_(file_format)
"""

from __future__ import annotations

from .reference import Reference


def format_ris_entry(ref: Reference) -> str:
    """Format a single reference as RIS entry.

    Uses TY - GEN (generic) as a safe default type.

    Args:
        ref: The reference to format.

    Returns:
        RIS entry string.
    """
    lines = []

    # Type of reference (GEN = generic)
    lines.append("TY  - GEN")

    # Title
    title = ref.title or ref.get_display_locator()
    lines.append(f"TI  - {title}")

    # Authors
    for author in ref.authors:
        lines.append(f"AU  - {author}")

    # Year
    if ref.year:
        lines.append(f"PY  - {ref.year}")

    # URL
    if ref.source_type == "url":
        url = ref.get_display_locator()
        lines.append(f"UR  - {url}")

    # Source type
    if ref.source_type == "pdf":
        lines.append("M3  - PDF")
    elif ref.source_type == "local":
        lines.append("M3  - Local file")

    # Pages
    pages_str = ref.get_pages_display()
    if pages_str:
        lines.append(f"SP  - {pages_str}")

    # Accessed date
    accessed = ref.accessed_at.strftime("%Y/%m/%d")
    lines.append(f"Y2  - {accessed}")

    # Notes (locator info)
    lines.append(f"N1  - {ref.locator}")

    # Database / Reference ID
    lines.append(f"ID  - {ref.id}")

    # End of record
    lines.append("ER  - ")

    return "\n".join(lines)


def export_ris(refs: list[Reference]) -> str:
    """Export references to RIS format.

    RIS is supported by:
    - Zotero
    - EndNote
    - Mendeley
    - RefWorks

    Args:
        refs: List of references to export.

    Returns:
        Complete RIS file content.
    """
    if not refs:
        return ""

    entries = [format_ris_entry(ref) for ref in refs]

    # Join with empty line between entries
    return "\n\n".join(entries) + "\n"