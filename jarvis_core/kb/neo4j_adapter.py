"""Neo4j adapter stub for knowledge base."""

from __future__ import annotations


class Neo4jAdapter:
    """Minimal Neo4j adapter."""

    def __init__(self, uri: str = "bolt://localhost:7687") -> None:
        """Initialize the adapter.

        Args:
            uri: Neo4j connection URI.
        """
        self.uri = uri

    def is_available(self) -> bool:
        """Return availability of the adapter.

        Returns:
            False for the stub implementation.
        """
        return False


__all__ = ["Neo4jAdapter"]
