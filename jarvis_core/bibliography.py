"""Bibliography utilities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BibliographyEntry:
    """Single bibliography entry."""

    title: str
    authors: list[str] = field(default_factory=list)


def format_entry(entry: BibliographyEntry) -> str:
    """Format a bibliography entry.

    Args:
        entry: Bibliography entry.

    Returns:
        Formatted string.
    """
    authors = ", ".join(entry.authors)
    return f"{authors}: {entry.title}" if authors else entry.title


__all__ = ["BibliographyEntry", "format_entry"]
