"""Chunking with provenance.

Per RP-05, chunks must have page/span locators.
"""

from __future__ import annotations

from typing import List, Tuple, Optional

from .models import ChunkRecord, Locator


def create_locator(
    pmid: Optional[str] = None,
    page: Optional[int] = None,
    span_start: Optional[int] = None,
    span_end: Optional[int] = None,
) -> str:
    """Create a locator string."""
    loc = Locator(
        pmid=pmid,
        page=page,
        span_start=span_start,
        span_end=span_end,
    )
    return loc.to_string()


def split_into_chunks(
    text: str,
    paper_id: str,
    page: int = 1,
    chunk_size: int = 1200,
    overlap: int = 200,
    pmid: Optional[str] = None,
    source: str = "pubmed",
) -> List[ChunkRecord]:
    """Split text into chunks with provenance.

    Args:
        text: Text to split.
        paper_id: Paper identifier.
        page: Page number.
        chunk_size: Characters per chunk.
        overlap: Character overlap between chunks.
        pmid: PubMed ID for locator.
        source: Source name.

    Returns:
        List of ChunkRecord with locators.
    """
    if not text.strip():
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        if not chunk_text.strip():
            start = end - overlap
            continue

        chunk = ChunkRecord.create(
            paper_id=paper_id,
            text=chunk_text,
            page=page,
            span_start=start,
            span_end=end,
            source=source,
            pmid=pmid,
        )
        chunks.append(chunk)

        start = end - overlap

    return chunks


def split_pages_into_chunks(
    pages: List[Tuple[int, str]],
    paper_id: str,
    chunk_size: int = 1200,
    overlap: int = 200,
    pmid: Optional[str] = None,
    source: str = "pubmed",
) -> List[ChunkRecord]:
    """Split multiple pages into chunks.

    Args:
        pages: List of (page_number, text) tuples.
        paper_id: Paper identifier.
        chunk_size: Characters per chunk.
        overlap: Character overlap.
        pmid: PubMed ID.
        source: Source name.

    Returns:
        List of all chunks with page-level locators.
    """
    all_chunks = []

    for page_num, page_text in pages:
        page_chunks = split_into_chunks(
            text=page_text,
            paper_id=paper_id,
            page=page_num,
            chunk_size=chunk_size,
            overlap=overlap,
            pmid=pmid,
            source=source,
        )
        all_chunks.extend(page_chunks)

    return all_chunks
