"""Reference formatter for academic citation styles.

This module provides:
- format_references(): Format references in Vancouver/APA style
- format_references_markdown(): Generate markdown reference list

Per RP14, this enables generating submittable reference lists
for academic documents.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from .reference import Reference


def format_vancouver(ref: Reference, index: int) -> str:
    """Format a reference in Vancouver style.

    Format: [N] Title. Source. Year. Available from: URL/path

    Args:
        ref: The reference to format.
        index: 1-based reference number.

    Returns:
        Formatted reference string.
    """
    parts = [f"[{index}]"]

    # Title or locator
    if ref.title:
        parts.append(f"{ref.title}.")
    else:
        parts.append(f"{ref.get_display_locator()}.")

    # Authors
    if ref.authors:
        author_str = ", ".join(ref.authors)
        parts.append(f"{author_str}.")

    # Year
    if ref.year:
        parts.append(f"{ref.year}.")

    # Pages
    pages_str = ref.get_pages_display()
    if pages_str:
        parts.append(f"{pages_str}.")

    # Source
    if ref.source_type == "url":
        url = ref.get_display_locator()
        parts.append(f"Available from: {url}")
    elif ref.source_type == "pdf":
        parts.append(f"[PDF] {ref.get_display_locator()}")
    else:
        parts.append(f"[Local] {ref.get_display_locator()}")

    # Accessed date
    accessed = ref.accessed_at.strftime("%Y-%m-%d")
    parts.append(f"[Accessed {accessed}]")

    return " ".join(parts)


def format_apa(ref: Reference, index: int) -> str:
    """Format a reference in APA style.

    Format: Author(s). (Year). Title. Retrieved from URL

    Args:
        ref: The reference to format.
        index: 1-based reference number (for consistency).

    Returns:
        Formatted reference string.
    """
    parts = []

    # Authors
    if ref.authors:
        if len(ref.authors) == 1:
            parts.append(f"{ref.authors[0]}.")
        elif len(ref.authors) == 2:
            parts.append(f"{ref.authors[0]} & {ref.authors[1]}.")
        else:
            parts.append(f"{ref.authors[0]} et al.")
    else:
        parts.append(f"[{ref.get_display_locator()}].")

    # Year
    if ref.year:
        parts.append(f"({ref.year}).")
    else:
        parts.append("(n.d.).")

    # Title
    if ref.title:
        parts.append(f"*{ref.title}*.")
    else:
        parts.append(f"*{ref.get_display_locator()}*.")

    # Pages
    pages_str = ref.get_pages_display()
    if pages_str:
        parts.append(f"({pages_str}).")

    # Source
    if ref.source_type == "url":
        url = ref.get_display_locator()
        parts.append(f"Retrieved from {url}")
    else:
        parts.append(f"[{ref.source_type.upper()}]")

    return " ".join(parts)


def format_references(
    refs: list[Reference],
    style: Literal["vancouver", "apa"] = "vancouver",
) -> str:
    """Format a list of references in the specified style.

    Args:
        refs: List of references to format.
        style: Citation style ("vancouver" or "apa").

    Returns:
        Formatted reference list as a string.
    """
    lines: list[str] = []

    formatter = format_vancouver if style == "vancouver" else format_apa

    for i, ref in enumerate(refs, 1):
        lines.append(formatter(ref, i))

    return "\n".join(lines)


def format_references_markdown(
    refs: list[Reference],
    style: Literal["vancouver", "apa"] = "vancouver",
) -> str:
    """Generate markdown reference list.

    Args:
        refs: List of references to format.
        style: Citation style ("vancouver" or "apa").

    Returns:
        Markdown formatted reference list.
    """
    style_name = "Vancouver" if style == "vancouver" else "APA"
    lines = [
        "# References",
        "",
        f"*Style: {style_name}*",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        "",
    ]

    formatter = format_vancouver if style == "vancouver" else format_apa

    for i, ref in enumerate(refs, 1):
        formatted = formatter(ref, i)
        lines.append(formatted)
        lines.append("")

    # Add mapping section
    lines.extend([
        "---",
        "",
        "## Chunk Mapping",
        "",
        "| Reference | Chunk IDs |",
        "|-----------|-----------|",
    ])

    for ref in refs:
        chunk_str = ", ".join(f"`{cid[:12]}...`" for cid in ref.chunk_ids[:3])
        if len(ref.chunk_ids) > 3:
            chunk_str += f" (+{len(ref.chunk_ids) - 3} more)"
        lines.append(f"| {ref.id} | {chunk_str} |")

    return "\n".join(lines)
