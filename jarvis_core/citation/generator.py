"""Citation generator shim."""

from __future__ import annotations


def generate_citation(title: str, year: int | None = None) -> str:
    """Generate a simple citation string.

    Args:
        title: Paper title.
        year: Publication year.

    Returns:
        Citation string.
    """
    suffix = f" ({year})" if year else ""
    return f"{title}{suffix}"
