"""Source adapter and chunker for Evidence ingestion pipeline.

This module provides:
- SourceDocument: Abstraction for external sources (local, url, pdf)
- Chunker: Splits documents into chunks for EvidenceStore
- ingest(): Pipeline to register chunks in EvidenceStore
- ChunkResult: Result of chunking
- ExecutionContext: Context available during task execution

Per RP6, this creates the "standard entry point" for populating
EvidenceStore with real content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from jarvis_core.evidence import EvidenceStore

SourceType = Literal["local", "url", "pdf"]


@dataclass
class SourceDocument:
    """Represents an external source document.

    Attributes:
        source: Type of source ("local", "url", "pdf")
        locator_base: Base locator for chunks (e.g., "file:...", "url:...")
        text: Extracted text content (assumed pre-extracted for MVP)
        metadata: Optional metadata dict
    """

    source: SourceType
    locator_base: str
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ChunkResult:
    """Result of chunking a document.

    Attributes:
        chunk_id: ID assigned by EvidenceStore
        locator: Full locator with chunk index (e.g., "file:...#chunk:0")
        preview: Preview of chunk content (first N chars)
    """

    chunk_id: str
    locator: str
    preview: str


class Chunker:
    """Splits text into chunks of approximately equal size.

    Attributes:
        chunk_size: Target size per chunk (characters)
        overlap: Overlap between chunks (characters)
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 100,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> list[str]:
        """Split text into chunks.

        Args:
            text: Full text to split.

        Returns:
            List of chunk texts.
        """
        if not text.strip():
            return []

        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size

            # If not at the end, try to break at a sentence boundary
            if end < text_len:
                # Look for sentence boundaries in the last 20% of chunk
                boundary_search_start = start + int(self.chunk_size * 0.8)
                boundary = self._find_sentence_boundary(text, boundary_search_start, end)
                if boundary > boundary_search_start:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.overlap if end < text_len else text_len

        return chunks

    def _find_sentence_boundary(self, text: str, search_start: int, search_end: int) -> int:
        """Find the last sentence boundary in the given range.

        Args:
            text: Full text.
            search_start: Start of search range.
            search_end: End of search range.

        Returns:
            Position after the sentence boundary, or search_end if not found.
        """
        # Look for sentence-ending punctuation followed by space or newline
        best_pos = search_end
        for char in ".!?。":
            pos = text.rfind(char, search_start, search_end)
            if pos > 0 and pos < best_pos:
                # Check if followed by space/newline or end of text
                if pos + 1 >= len(text) or text[pos + 1] in " \n\t":
                    best_pos = pos + 1

        return best_pos if best_pos < search_end else search_end


def ingest(
    document: SourceDocument,
    store: EvidenceStore,
    chunker: Chunker | None = None,
    preview_length: int = 100,
) -> list[ChunkResult]:
    """Ingest a document into EvidenceStore.

    This is the main entry point for populating EvidenceStore with
    content from external sources.

    Args:
        document: The source document to ingest.
        store: The EvidenceStore to populate.
        chunker: Optional Chunker instance (uses default if None).
        preview_length: Length of preview text in results.

    Returns:
        List of ChunkResult with chunk_id, locator, and preview.
    """
    if chunker is None:
        chunker = Chunker()

    chunks = chunker.split(document.text)
    results: list[ChunkResult] = []

    for i, chunk_text in enumerate(chunks):
        locator = f"{document.locator_base}#chunk:{i}"

        chunk_id = store.add_chunk(
            source=document.source,
            locator=locator,
            text=chunk_text,
        )

        preview = chunk_text[:preview_length]
        if len(chunk_text) > preview_length:
            preview = preview.rstrip() + "..."

        results.append(
            ChunkResult(
                chunk_id=chunk_id,
                locator=locator,
                preview=preview,
            )
        )

    return results


@dataclass
class ExecutionContext:
    """Context available during Task execution.

    This provides agents with access to available evidence chunks
    for citation purposes.

    Attributes:
        evidence_store: The EvidenceStore for this Task.
        available_chunks: List of available chunks for citation.
    """

    evidence_store: EvidenceStore
    available_chunks: list[ChunkResult] = field(default_factory=list)

    def add_chunks(self, chunks: list[ChunkResult]) -> None:
        """Add chunks to available list."""
        self.available_chunks.extend(chunks)

    def get_chunk_ids(self) -> list[str]:
        """Get list of available chunk_ids."""
        return [c.chunk_id for c in self.available_chunks]

    def get_chunks_preview(self) -> list[dict]:
        """Get list of chunks with preview info for agent prompts."""
        return [
            {
                "chunk_id": c.chunk_id,
                "locator": c.locator,
                "preview": c.preview,
            }
            for c in self.available_chunks
        ]

    def get_relevant_chunks(
        self,
        query: str,
        k: int = 8,
    ) -> list[ChunkResult]:
        """Get relevant chunks for a query using retrieval.

        Uses BM25 retrieval if there are many chunks,
        otherwise returns all chunks.

        Args:
            query: The search query.
            k: Maximum number of results.

        Returns:
            List of relevant ChunkResult.
        """
        # Avoid circular import by importing here
        from jarvis_core.retriever import get_relevant_chunks as retrieve

        return retrieve(
            query=query,
            chunks=self.available_chunks,
            store=self.evidence_store,
            k=k,
        )

    def get_relevant_chunks_preview(
        self,
        query: str,
        k: int = 8,
    ) -> list[dict]:
        """Get relevant chunks preview for agent prompts.

        Args:
            query: The search query.
            k: Maximum number of results.

        Returns:
            List of chunk preview dicts for agent.
        """
        relevant = self.get_relevant_chunks(query, k=k)
        return [
            {
                "chunk_id": c.chunk_id,
                "locator": c.locator,
                "preview": c.preview,
            }
            for c in relevant
        ]

    def get_relevant_chunks_vector(
        self,
        query: str,
        k: int = 8,
    ) -> list[ChunkResult]:
        """Get relevant chunks using vector similarity.

        Uses embedding-based semantic search instead of BM25.

        Args:
            query: The search query.
            k: Maximum number of results.

        Returns:
            List of ChunkResult objects sorted by similarity.
        """
        # Avoid circular import
        from jarvis_core.vector_index import get_relevant_chunks_vector

        if not self.available_chunks:
            return []

        return get_relevant_chunks_vector(
            self.available_chunks,
            query,
            k=k,
        )
