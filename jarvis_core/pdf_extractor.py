"""PDF extractor and adapter for Evidence ingestion pipeline.

This module provides:
- extract_pdf_pages(): Extract text from PDF pages using PyMuPDF
- load_pdf_as_documents(): Convert PDF pages to SourceDocuments

Per RP7, this creates the standard entry point for ingesting
PDF documents (papers) into EvidenceStore.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TypedDict

from .sources import SourceDocument

logger = logging.getLogger("jarvis_core.pdf_extractor")


class PageContent(TypedDict):
    """Content of a single PDF page."""

    page: int
    text: str


def extract_pdf_pages(pdf_path: str | Path) -> list[PageContent]:
    """Extract text from each page of a PDF.

    Uses PyMuPDF (fitz) for extraction. Each page is extracted
    separately to enable page-level citations.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of PageContent dicts with page number and text.
        Empty pages are included with empty text string.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        RuntimeError: If PDF cannot be opened.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise ImportError(
            "PyMuPDF is required for PDF extraction. " "Install with: pip install pymupdf"
        ) from e

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pages: list[PageContent] = []

    try:
        doc = fitz.open(str(path))
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF: {pdf_path}") from e

    try:
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                text = page.get_text()
            except Exception as e:
                logger.warning(
                    "Failed to extract page %d from %s: %s",
                    page_num + 1,
                    pdf_path,
                    e,
                )
                text = ""

            pages.append(
                PageContent(
                    page=page_num + 1,  # 1-indexed
                    text=text.strip() if text else "",
                )
            )
    finally:
        doc.close()

    return pages


def load_pdf_as_documents(
    pdf_path: str | Path,
    normalize_path: bool = True,
) -> list[SourceDocument]:
    """Load a PDF as a list of SourceDocuments (one per page).

    Each page becomes a separate SourceDocument for fine-grained
    citations. The locator_base includes page information.

    Args:
        pdf_path: Path to the PDF file.
        normalize_path: If True, use absolute path in locator.

    Returns:
        List of SourceDocument, one per page.
    """
    path = Path(pdf_path)
    if normalize_path:
        path = path.resolve()

    pages = extract_pdf_pages(path)
    documents: list[SourceDocument] = []

    for page_content in pages:
        page_num = page_content["page"]
        text = page_content["text"]

        # locator_base includes page info for stable citations
        locator_base = f"pdf:{path}#page:{page_num}"

        doc = SourceDocument(
            source="pdf",
            locator_base=locator_base,
            text=text,
            metadata={
                "page": page_num,
                "total_pages": len(pages),
                "source_file": str(path),
            },
        )
        documents.append(doc)

    return documents


def ingest_pdf(
    pdf_path: str | Path,
    store: EvidenceStore,
    context: ExecutionContext | None = None,
) -> list[ChunkResult]:
    """Convenience function to ingest a PDF into EvidenceStore.

    This is the recommended way to add PDF content to EvidenceStore.
    It handles extraction, document creation, and chunk registration.

    Args:
        pdf_path: Path to the PDF file.
        store: The EvidenceStore to populate.
        context: Optional ExecutionContext to register chunks in.

    Returns:
        List of all ChunkResults from the PDF.
    """
    from .sources import ChunkResult, ingest

    documents = load_pdf_as_documents(pdf_path)
    all_results: list[ChunkResult] = []

    for doc in documents:
        # Preview includes page info
        page_num = doc.metadata.get("page", "?")
        results = ingest(doc, store, preview_length=80)

        # Enhance preview with page info
        for result in results:
            result.preview = f"[p.{page_num}] {result.preview}"

        all_results.extend(results)

    if context is not None:
        context.add_chunks(all_results)

    return all_results
