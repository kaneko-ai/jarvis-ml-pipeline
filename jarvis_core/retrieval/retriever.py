"""Retriever helpers."""

from __future__ import annotations


class Retriever:
    """Minimal retriever stub."""

    def retrieve(self, query: str) -> list[str]:
        """Retrieve documents for a query.

        Args:
            query: Query string.

        Returns:
            List of document identifiers.
        """
        _ = query
        return []


__all__ = ["Retriever"]
