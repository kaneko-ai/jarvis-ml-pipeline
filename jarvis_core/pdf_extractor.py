"""PDF extractor and adapter for Evidence ingestion pipeline.

This module provides:
- extract_pdf_pages(): Extract text from PDF pages using PyMuPDF
- load_pdf_as_documents(): Convert PDF pages to SourceDocuments

Per RP7, this creates the standard entry point for ingesting
PDF documents (papers) into EvidenceStore.
"""

from __future__ import annotations

import base64
import logging
import re
import zlib
from pathlib import Path
from typing import Any, TYPE_CHECKING, TypedDict

from .sources import SourceDocument

if TYPE_CHECKING:
    from jarvis_core.evidence import EvidenceStore
    from jarvis_core.sources import ChunkResult, ExecutionContext

logger = logging.getLogger("jarvis_core.pdf_extractor")


class PageContent(TypedDict):
    """Content of a single PDF page."""

    page: int
    text: str


def _get_fitz_module() -> Any | None:
    """Return PyMuPDF module when available and not stubbed."""
    try:
        import fitz  # type: ignore
    except ImportError:
        return None
    if getattr(fitz, "__jarvis_stub__", False):
        return None
    return fitz


def _iter_pdf_streams(data: bytes) -> list[bytes]:
    """Extract raw PDF streams (between stream/endstream)."""
    streams: list[bytes] = []
    for match in re.finditer(rb"stream\r?\n", data):
        start = match.end()
        end = data.find(b"endstream", start)
        if end == -1:
            continue
        streams.append(data[start:end].strip(b"\r\n"))
    return streams


def _decode_stream(raw: bytes) -> bytes | None:
    """Best-effort decode of a PDF content stream."""
    if not raw:
        return None
    # Try ASCII85 + Flate (ReportLab default)
    try:
        decoded = base64.a85decode(raw, adobe=True)
        return zlib.decompress(decoded)
    except (ValueError, zlib.error, TypeError) as exc:
        logger.debug("ASCII85+Flate decode failed: %s", exc)
    # Try Flate only
    try:
        return zlib.decompress(raw)
    except zlib.error as exc:
        logger.debug("Flate decode failed: %s", exc)
    # Try ASCII85 only
    try:
        return base64.a85decode(raw, adobe=True)
    except (ValueError, TypeError) as exc:
        logger.debug("ASCII85 decode failed: %s", exc)
        return None


def _unescape_pdf_string(raw: bytes) -> str:
    """Unescape a PDF string literal."""
    out = bytearray()
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == 0x5C:  # backslash
            i += 1
            if i >= len(raw):
                break
            esc = raw[i]
            if esc in b"nrtbf":
                mapping = {
                    ord("n"): b"\n",
                    ord("r"): b"\r",
                    ord("t"): b"\t",
                    ord("b"): b"\b",
                    ord("f"): b"\f",
                }
                out.extend(mapping[esc])
            elif esc in b"\\()":
                out.append(esc)
            elif 0x30 <= esc <= 0x37:
                oct_digits = bytes([esc])
                j = i + 1
                for _ in range(2):
                    if j < len(raw) and 0x30 <= raw[j] <= 0x37:
                        oct_digits += bytes([raw[j]])
                        i = j
                        j += 1
                    else:
                        break
                out.append(int(oct_digits, 8))
            else:
                out.append(esc)
        else:
            out.append(ch)
        i += 1
    return out.decode("latin-1", errors="ignore")


def _extract_text_from_stream(decoded: bytes) -> str:
    """Extract text from a decoded content stream."""
    texts: list[str] = []
    for match in re.finditer(rb"\((?:\\.|[^\\)])*\)", decoded):
        raw = match.group()[1:-1]
        text = _unescape_pdf_string(raw).strip()
        if text:
            texts.append(text)
    return " ".join(texts).strip()


def _extract_pdf_pages_fallback(path: Path) -> list[PageContent]:
    """Fallback PDF extraction using standard library only."""
    data = path.read_bytes()
    pages: list[PageContent] = []
    for stream in _iter_pdf_streams(data):
        decoded = _decode_stream(stream)
        if not decoded:
            continue
        text = _extract_text_from_stream(decoded)
        if text:
            pages.append(PageContent(page=len(pages) + 1, text=text))
    if not pages:
        raise RuntimeError(f"Failed to extract PDF text without PyMuPDF: {path}")
    return pages


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
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    fitz = _get_fitz_module()
    if fitz is None:
        return _extract_pdf_pages_fallback(path)

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
    from .sources import ingest

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
