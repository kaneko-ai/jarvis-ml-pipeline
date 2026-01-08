"""Contextual Embeddings.

Per RP-301, generates embeddings with surrounding context.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ContextualChunk:
    """Chunk with contextual information."""

    chunk_id: str
    text: str
    context_prefix: str  # Section title, previous sentence
    context_suffix: str  # Following sentence
    metadata: dict[str, Any]


class ContextualEmbedder:
    """Generates embeddings with contextual awareness.
    
    Per RP-301:
    - Integrates surrounding chunk context
    - Prefixes section titles
    - Incorporates paper metadata
    """

    def __init__(
        self,
        base_embedder=None,
        include_section: bool = True,
        include_metadata: bool = True,
        context_window: int = 1,
    ):
        self.base_embedder = base_embedder
        self.include_section = include_section
        self.include_metadata = include_metadata
        self.context_window = context_window

    def prepare_contextual_text(
        self,
        chunk: ContextualChunk,
        paper_metadata: dict[str, Any] | None = None,
    ) -> str:
        """Prepare text with context for embedding.
        
        Args:
            chunk: The chunk to embed.
            paper_metadata: Optional paper metadata (year, journal, etc.).
            
        Returns:
            Contextualized text string.
        """
        parts = []

        # Add metadata prefix
        if self.include_metadata and paper_metadata:
            year = paper_metadata.get("year", "")
            journal = paper_metadata.get("journal", "")
            if year or journal:
                parts.append(f"[{year} {journal}]".strip())

        # Add section prefix
        if self.include_section and chunk.context_prefix:
            parts.append(f"[Section: {chunk.context_prefix}]")

        # Add main text
        parts.append(chunk.text)

        # Add context suffix
        if chunk.context_suffix:
            parts.append(f"[Context: {chunk.context_suffix[:100]}]")

        return " ".join(parts)

    def embed(
        self,
        chunks: list[ContextualChunk],
        paper_metadata: dict[str, Any] | None = None,
    ) -> list[list[float]]:
        """Generate contextual embeddings.
        
        Args:
            chunks: List of chunks to embed.
            paper_metadata: Optional paper metadata.
            
        Returns:
            List of embedding vectors.
        """
        # Prepare contextualized texts
        texts = [
            self.prepare_contextual_text(chunk, paper_metadata)
            for chunk in chunks
        ]

        # Use base embedder if available
        if self.base_embedder:
            return self.base_embedder.embed(texts)

        # Fallback: return placeholder
        return [[0.0] * 384 for _ in texts]

    def add_context_to_chunks(
        self,
        chunks: list[dict[str, Any]],
        sections: list[dict[str, Any]] | None = None,
    ) -> list[ContextualChunk]:
        """Add context information to raw chunks.
        
        Args:
            chunks: List of raw chunk dicts.
            sections: Optional section information.
            
        Returns:
            List of ContextualChunk objects.
        """
        contextual = []

        for i, chunk in enumerate(chunks):
            # Get previous chunk text for context
            prev_text = ""
            if i > 0 and self.context_window > 0:
                prev_chunk = chunks[i - 1]
                prev_text = prev_chunk.get("text", "")[-100:]

            # Get next chunk text for context
            next_text = ""
            if i < len(chunks) - 1 and self.context_window > 0:
                next_chunk = chunks[i + 1]
                next_text = next_chunk.get("text", "")[:100]

            # Determine section title
            section_title = chunk.get("section_title", "")
            if not section_title and sections:
                chunk_start = chunk.get("start_char", 0)
                for section in sections:
                    if section.get("start", 0) <= chunk_start < section.get("end", float("inf")):
                        section_title = section.get("title", "")
                        break

            contextual.append(ContextualChunk(
                chunk_id=chunk.get("chunk_id", str(i)),
                text=chunk.get("text", ""),
                context_prefix=section_title or prev_text[:50],
                context_suffix=next_text,
                metadata=chunk.get("metadata", {}),
            ))

        return contextual
