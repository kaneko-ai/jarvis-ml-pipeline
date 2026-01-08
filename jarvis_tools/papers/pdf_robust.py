"""PDF Robust Extractor.

Per RP-108, provides PDF extraction with fallback chain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from jarvis_core.runtime.result import Result, ErrorRecord


class PDFEngine(Enum):
    """PDF extraction engine."""

    PYMUPDF = "pymupdf"
    PDFMINER = "pdfminer"
    PYPDF2 = "pypdf2"


@dataclass
class PDFExtractResult:
    """Result of PDF extraction."""

    text: str
    engine_used: PDFEngine
    page_count: int
    char_count: int
    warnings: List[str]


@dataclass
class EngineFailure:
    """Record of engine failure."""

    engine: PDFEngine
    error_type: str
    error_message: str


def extract_with_pymupdf(pdf_path: str) -> Result[PDFExtractResult]:
    """Extract using PyMuPDF (fitz)."""
    try:
        import fitz

        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())

        text = "\n".join(text_parts)
        page_count = len(doc)
        doc.close()

        return Result.success(PDFExtractResult(
            text=text,
            engine_used=PDFEngine.PYMUPDF,
            page_count=page_count,
            char_count=len(text),
            warnings=[],
        ))

    except ImportError:
        return Result.fail(ErrorRecord(
            error_type="ImportError",
            message="PyMuPDF not installed",
            recoverable=True,
        ))
    except Exception as e:
        return Result.fail(ErrorRecord(
            error_type=type(e).__name__,
            message=str(e),
            recoverable=True,
        ))


def extract_with_pdfminer(pdf_path: str) -> Result[PDFExtractResult]:
    """Extract using pdfminer."""
    try:
        from pdfminer.high_level import extract_text

        text = extract_text(pdf_path)

        return Result.success(PDFExtractResult(
            text=text,
            engine_used=PDFEngine.PDFMINER,
            page_count=0,  # pdfminer doesn't easily give page count
            char_count=len(text),
            warnings=[],
        ))

    except ImportError:
        return Result.fail(ErrorRecord(
            error_type="ImportError",
            message="pdfminer not installed",
            recoverable=True,
        ))
    except Exception as e:
        return Result.fail(ErrorRecord(
            error_type=type(e).__name__,
            message=str(e),
            recoverable=True,
        ))


def extract_with_pypdf2(pdf_path: str) -> Result[PDFExtractResult]:
    """Extract using PyPDF2."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")

        text = "\n".join(text_parts)

        return Result.success(PDFExtractResult(
            text=text,
            engine_used=PDFEngine.PYPDF2,
            page_count=len(reader.pages),
            char_count=len(text),
            warnings=[],
        ))

    except ImportError:
        return Result.fail(ErrorRecord(
            error_type="ImportError",
            message="PyPDF2 not installed",
            recoverable=True,
        ))
    except Exception as e:
        return Result.fail(ErrorRecord(
            error_type=type(e).__name__,
            message=str(e),
            recoverable=True,
        ))


# Engine chain (order of fallback)
ENGINE_CHAIN = [
    (PDFEngine.PYMUPDF, extract_with_pymupdf),
    (PDFEngine.PDFMINER, extract_with_pdfminer),
    (PDFEngine.PYPDF2, extract_with_pypdf2),
]


@dataclass
class ChainExtractResult:
    """Result of chain extraction."""

    result: Optional[PDFExtractResult]
    failures: List[EngineFailure]
    success: bool


def extract_pdf_with_chain(pdf_path: str) -> ChainExtractResult:
    """Extract PDF using engine chain with fallbacks.

    Tries each engine in order until one succeeds.

    Args:
        pdf_path: Path to PDF file.

    Returns:
        ChainExtractResult with result or failure details.
    """
    failures = []

    for engine, extract_fn in ENGINE_CHAIN:
        result = extract_fn(pdf_path)

        if result.is_success:
            return ChainExtractResult(
                result=result.value,
                failures=failures,
                success=True,
            )
        else:
            failures.append(EngineFailure(
                engine=engine,
                error_type=result.error.error_type if result.error else "Unknown",
                error_message=result.error.message if result.error else "",
            ))

    return ChainExtractResult(
        result=None,
        failures=failures,
        success=False,
    )
