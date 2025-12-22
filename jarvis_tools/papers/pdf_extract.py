"""PDF text extraction.

Per RP-04, extracted from run_pipeline.py with page tracking.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """Extract text from PDF with page numbers.

    Args:
        pdf_path: Path to PDF file.

    Returns:
        List of (page_number, text) tuples.
    """
    path = Path(pdf_path)
    if not path.exists():
        return []

    pages = []

    # Try PyMuPDF first (better quality)
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(path))
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():
                pages.append((page_num, text))
        doc.close()
        return pages

    except ImportError:
        pass

    # Fall back to PyPDF2
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((page_num, text))
        return pages

    except Exception as e:
        print(f"[extract_text_from_pdf] Error: {e}")
        return []


def extract_full_text(pdf_path: str) -> str:
    """Extract full text from PDF (all pages concatenated)."""
    pages = extract_text_from_pdf(pdf_path)
    return "\n\n".join(text for _, text in pages)
