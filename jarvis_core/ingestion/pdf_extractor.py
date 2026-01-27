"""Hardened PDF Extractor for JARVIS (Phase 22).

Handles limits on page counts and file sizes, and provides detailed error reporting.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.ingestion.pdf")


@dataclass
class PDFFailureInfo:
    """Detailed information about an extraction failure."""

    file_path: str
    error_code: str
    message: str
    details: dict = field(default_factory=dict)


class HardenedPDFExtractor:
    """PDF text extractor with safety limits and detailed diagnostics."""

    def __init__(
        self, max_pages: int = 200, max_file_size_mb: int = 100, extract_images: bool = False
    ):
        self.max_pages = max_pages
        self.max_file_size_mb = max_file_size_mb
        self.extract_images = extract_images
        self._backends = self._init_backends()

    def _init_backends(self):
        backends = {}
        try:
            import fitz

            backends["pymupdf"] = fitz
        except ImportError:
            pass
        try:
            import pdfplumber

            backends["pdfplumber"] = pdfplumber
        except ImportError:
            pass
        return backends

    def extract(self, path: Path) -> Tuple[str, List[Tuple[int, str]], Optional[PDFFailureInfo]]:
        """Extract text from PDF with safety checks."""
        # 1. File size check
        if not path.exists():
            return "", [], PDFFailureInfo(str(path), "FILE_NOT_FOUND", "File does not exist")

        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return (
                "",
                [],
                PDFFailureInfo(
                    str(path),
                    "LIMIT_EXCEEDED",
                    f"File size {file_size_mb:.1f}MB exceeds limit {self.max_file_size_mb}MB",
                ),
            )

        # 2. Try extraction using primary backend (PyMuPDF)
        if "pymupdf" in self._backends:
            return self._extract_pymupdf(path)
        elif "pdfplumber" in self._backends:
            return self._extract_pdfplumber(path)
        else:
            return "", [], PDFFailureInfo(str(path), "MISSING_BACKEND", "No PDF backend installed")

    def _extract_pymupdf(
        self, path: Path
    ) -> Tuple[str, List[Tuple[int, str]], Optional[PDFFailureInfo]]:
        fitz = self._backends["pymupdf"]
        pages_content = []
        all_text = []

        try:
            with fitz.open(path) as doc:
                # 3. Page count check
                if len(doc) > self.max_pages:
                    return (
                        "",
                        [],
                        PDFFailureInfo(
                            str(path),
                            "LIMIT_EXCEEDED",
                            f"Page count {len(doc)} exceeds limit {self.max_pages}",
                        ),
                    )

                for i, page in enumerate(doc):
                    text = page.get_text()
                    pages_content.append((i + 1, text))
                    all_text.append(text)

            return "\n\n".join(all_text), pages_content, None
        except Exception as e:
            return "", [], PDFFailureInfo(str(path), "EXTRACT_ERROR", str(e))

    def _extract_pdfplumber(
        self, path: Path
    ) -> Tuple[str, List[Tuple[int, str]], Optional[PDFFailureInfo]]:
        pdfplumber = self._backends["pdfplumber"]
        pages_content = []
        all_text = []

        try:
            with pdfplumber.open(path) as pdf:
                if len(pdf.pages) > self.max_pages:
                    return (
                        "",
                        [],
                        PDFFailureInfo(
                            str(path),
                            "LIMIT_EXCEEDED",
                            f"Page count {len(pdf.pages)} exceeds limit {self.max_pages}",
                        ),
                    )

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages_content.append((i + 1, text))
                    all_text.append(text)

            return "\n\n".join(all_text), pages_content, None
        except Exception as e:
            return "", [], PDFFailureInfo(str(path), "EXTRACT_ERROR", str(e))
