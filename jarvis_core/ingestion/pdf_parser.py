"""Parse PDF full-text into structured sections."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Section:
    title: str
    text: str


@dataclass
class ParsedPaper:
    title: str
    abstract: str
    sections: list[Section] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)


def parse_pdf(pdf_path: Path) -> ParsedPaper:
    """Parse a PDF into a structured ParsedPaper.

    Args:
        pdf_path: Path to PDF.

    Returns:
        ParsedPaper with extracted fields.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - dependency optional
        raise RuntimeError("PyMuPDF is required for PDF parsing") from exc

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    text_pages = [page.get_text("text") for page in doc]
    doc.close()

    full_text = "\n".join(text_pages)
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]

    title = lines[0] if lines else ""
    abstract = _extract_abstract(lines)
    sections = _extract_sections(lines)
    references = _extract_references(lines)

    return ParsedPaper(
        title=title,
        abstract=abstract,
        sections=sections,
        references=references,
        tables=[],
        figures=[],
    )


def _extract_abstract(lines: Iterable[str]) -> str:
    abstract_lines = []
    capture = False
    for line in lines:
        lower = line.lower()
        if lower.startswith("abstract"):
            capture = True
            abstract_lines.append(line.split(":", 1)[-1].strip() or line)
            continue
        if capture and (line.isupper() or line.endswith(".")):
            abstract_lines.append(line)
        if capture and (lower.startswith("introduction") or lower.startswith("methods")):
            break
    return " ".join(abstract_lines).strip()


def _extract_sections(lines: Iterable[str]) -> list[Section]:
    sections: list[Section] = []
    current_title = ""
    current_lines: list[str] = []

    def flush():
        nonlocal current_title, current_lines
        if current_title or current_lines:
            sections.append(Section(title=current_title or "Section", text=" ".join(current_lines).strip()))
        current_title = ""
        current_lines = []

    for line in lines:
        if line.isupper() and len(line.split()) < 6:
            flush()
            current_title = line.title()
        else:
            current_lines.append(line)
    flush()
    return sections


def _extract_references(lines: Iterable[str]) -> list[str]:
    refs = []
    in_refs = False
    for line in lines:
        if line.lower().startswith("references"):
            in_refs = True
            continue
        if in_refs:
            refs.append(line)
    return refs
