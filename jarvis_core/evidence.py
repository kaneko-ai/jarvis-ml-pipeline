"""Evidence store for Task-scoped chunk management.

Per JARVIS_MASTER.md, EvidenceStore is the single source of truth for
citations within a Task execution. All chunks (evidence) referenced
by agents must be registered here, and ExecutionEngine validates
citations against this store.

Key properties:
- Task-scoped: One EvidenceStore per run_jarvis() invocation
- In-memory: No persistence (RP5 scope)
- Agent-agnostic: ExecutionEngine manages; agents only reference chunk_ids
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class Chunk:
    """A piece of evidence that can be cited.

    Chunks are the atomic units of evidence. Each chunk has:
    - chunk_id: Unique identifier (UUID)
    - source: Origin type ("local", "web", "pdf", etc.)
    - locator: Precise location ("page:3", "url:...", "pmid:...")
    - text: The actual content
    """

    chunk_id: str
    source: str
    locator: str
    text: str


class EvidenceStore:
    """In-memory store for Task-scoped evidence chunks.

    This is the single source of truth for citations within a Task.
    Agents register chunks here; ExecutionEngine validates citations
    against this store.

    Usage:
        store = EvidenceStore()
        chunk_id = store.add_chunk("pdf", "page:5", "CD73 is expressed...")
        chunk = store.get_chunk(chunk_id)
    """

    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}

    def add_chunk(self, source: str, locator: str, text: str) -> str:
        """Register a new evidence chunk.

        Args:
            source: Origin type ("local", "web", "pdf", etc.)
            locator: Precise location ("page:3", "url:...", "pmid:...")
            text: The actual content.

        Returns:
            Unique chunk_id for referencing this chunk.
        """
        chunk_id = str(uuid.uuid4())
        self._chunks[chunk_id] = Chunk(
            chunk_id=chunk_id,
            source=source,
            locator=locator,
            text=text,
        )
        return chunk_id

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Retrieve a chunk by its ID.

        Args:
            chunk_id: The unique identifier.

        Returns:
            The Chunk if found, None otherwise.
        """
        return self._chunks.get(chunk_id)

    def has_chunk(self, chunk_id: str) -> bool:
        """Check if a chunk exists.

        Args:
            chunk_id: The unique identifier.

        Returns:
            True if the chunk exists.
        """
        return chunk_id in self._chunks

    def get_quote(self, chunk_id: str, max_length: int = 100) -> str:
        """Generate a quote from a chunk.

        This is the authoritative source for citation quotes.
        Agents should NOT generate quotes; this method does.

        Args:
            chunk_id: The chunk to quote from.
            max_length: Maximum quote length (default 100 chars).

        Returns:
            Quote text, or empty string if chunk not found.
        """
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return ""
        text = chunk.text.strip()
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def list_chunks(self) -> list[Chunk]:
        """List all registered chunks.

        Returns:
            List of all Chunk objects.
        """
        return list(self._chunks.values())

    def __len__(self) -> int:
        return len(self._chunks)
