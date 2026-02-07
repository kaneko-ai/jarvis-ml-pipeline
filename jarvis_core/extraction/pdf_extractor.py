"""
JARVIS PDF Extractor

1. PDF蜈ｨ譁・歓蜃ｺ: 隲匁枚PDF縺九ｉ讒矩蛹悶ユ繧ｭ繧ｹ繝医ｒ謚ｽ蜃ｺ
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import fitz as fitz
except Exception:  # pragma: no cover - optional dependency
    fitz = None

logger = logging.getLogger(__name__)


@dataclass
class PDFSection:
    """PDF繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ."""

    title: str
    content: str
    page: int
    section_type: str  # abstract, introduction, methods, results, discussion, references

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "page": self.page,
            "section_type": self.section_type,
        }


@dataclass
class PDFDocument:
    """謚ｽ蜃ｺ貂医∩PDF繝峨く繝･繝｡繝ｳ繝・"""

    path: str
    title: str
    authors: list[str]
    abstract: str
    sections: list[PDFSection] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    figures: list[dict[str, str]] = field(default_factory=list)
    tables: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "sections": [s.to_dict() for s in self.sections],
            "references": self.references,
            "figures": self.figures,
            "tables": self.tables,
        }

    def get_full_text(self) -> str:
        """蜈ｨ譁・ｒ蜿門ｾ・"""
        parts = [self.abstract]
        for section in self.sections:
            parts.append(f"\n## {section.title}\n{section.content}")
        return "\n".join(parts)


class PDFExtractor:
    """PDF謚ｽ蜃ｺ蝎ｨ.

    PyMuPDF (fitz) 繧剃ｽｿ逕ｨ縺励※PDF縺九ｉ繝・く繧ｹ繝医ｒ謚ｽ蜃ｺ
    """

    SECTION_PATTERNS = {
        "abstract": r"(?i)^(abstract|summary)$",
        "introduction": r"(?i)^(introduction|background)$",
        "methods": r"(?i)^(methods?|materials?\s*(and|&)\s*methods?|experimental)$",
        "results": r"(?i)^(results?|findings?)$",
        "discussion": r"(?i)^(discussion|conclusions?|concluding\s*remarks?)$",
        "references": r"(?i)^(references?|bibliography|citations?)$",
    }

    def __init__(self):
        """蛻晄悄蛹・"""
        self._fitz = None

    def _get_fitz(self):
        """PyMuPDF繧帝≦蟒ｶ繝ｭ繝ｼ繝・"""
        if self._fitz is None:
            if fitz is not None:
                self._fitz = fitz
            else:
                try:
                    import fitz as fitz_runtime

                    self._fitz = fitz_runtime
                except ImportError:
                    logger.warning("PyMuPDF not installed. Install with: pip install pymupdf")
                    self._fitz = None
        return self._fitz

    def extract(self, pdf_path: str) -> PDFDocument:
        """PDF縺九ｉ繝・く繧ｹ繝医ｒ謚ｽ蜃ｺ.

        Args:
            pdf_path: PDF繝輔ぃ繧､繝ｫ繝代せ

        Returns:
            謚ｽ蜃ｺ貂医∩繝峨く繝･繝｡繝ｳ繝・
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        fitz = self._get_fitz()

        if fitz is None:
            # Fallback: 蝓ｺ譛ｬ逧・↑繝・く繧ｹ繝域歓蜃ｺ
            return self._extract_fallback(pdf_path)

        return self._extract_with_fitz(pdf_path, fitz)

    def _extract_with_fitz(self, pdf_path: str, fitz) -> PDFDocument:
        """PyMuPDF縺ｧ謚ｽ蜃ｺ."""
        doc = fitz.open(pdf_path)

        # 繝｡繧ｿ繝・・繧ｿ
        metadata = doc.metadata
        title = metadata.get("title", "") or Path(pdf_path).stem
        authors = metadata.get("author", "").split(",")

        # 蜈ｨ繝壹・繧ｸ縺ｮ繝・く繧ｹ繝・
        full_text = ""
        page_texts = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            page_texts.append((page_num + 1, text))
            full_text += text + "\n"

        doc.close()

        # 繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ蛻・牡
        sections = self._parse_sections(page_texts)

        # Abstract謚ｽ蜃ｺ
        abstract = ""
        for section in sections:
            if section.section_type == "abstract":
                abstract = section.content
                break

        # 蜿り・枚迪ｮ謚ｽ蜃ｺ
        references = self._extract_references(full_text)

        return PDFDocument(
            path=pdf_path,
            title=title,
            authors=authors,
            abstract=abstract,
            sections=sections,
            references=references,
        )

    def _extract_fallback(self, pdf_path: str) -> PDFDocument:
        """繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ謚ｽ蜃ｺ・・yMuPDF縺ｪ縺暦ｼ・"""
        logger.warning("Using fallback extraction (limited functionality)")

        return PDFDocument(
            path=pdf_path,
            title=Path(pdf_path).stem,
            authors=[],
            abstract="",
            sections=[],
            references=[],
        )

    def _parse_sections(self, page_texts: list[tuple]) -> list[PDFSection]:
        """繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繧貞・蜑ｲ."""
        sections = []
        current_section = None
        current_content = []
        current_page = 1

        for page_num, text in page_texts:
            lines = text.split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繝倥ャ繝繝ｼ繧呈､懷・
                section_type = self._detect_section_type(line)

                if section_type:
                    # 蜑阪・繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繧剃ｿ晏ｭ・
                    if current_section:
                        sections.append(
                            PDFSection(
                                title=current_section,
                                content="\n".join(current_content),
                                page=current_page,
                                section_type=self._get_section_type(current_section),
                            )
                        )

                    current_section = line
                    current_content = []
                    current_page = page_num
                else:
                    current_content.append(line)

        # 譛蠕後・繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ
        if current_section:
            sections.append(
                PDFSection(
                    title=current_section,
                    content="\n".join(current_content),
                    page=current_page,
                    section_type=self._get_section_type(current_section),
                )
            )

        return sections

    def _detect_section_type(self, line: str) -> str | None:
        """繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繧ｿ繧､繝励ｒ讀懷・."""
        for section_type, pattern in self.SECTION_PATTERNS.items():
            if re.match(pattern, line):
                return section_type
        return None

    def _get_section_type(self, title: str) -> str:
        """繧ｿ繧､繝医Ν縺九ｉ繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繧ｿ繧､繝励ｒ蜿門ｾ・"""
        for section_type, pattern in self.SECTION_PATTERNS.items():
            if re.match(pattern, title):
                return section_type
        return "other"

    def _extract_references(self, text: str) -> list[str]:
        """蜿り・枚迪ｮ繧呈歓蜃ｺ."""
        references = []

        # DOI繝代ち繝ｼ繝ｳ
        dois = re.findall(r"10\.\d{4,}/[^\s]+", text)
        references.extend([f"DOI: {doi}" for doi in dois[:20]])

        # PMID繝代ち繝ｼ繝ｳ
        pmids = re.findall(r"PMID[:\s]*(\d+)", text, re.IGNORECASE)
        references.extend([f"PMID: {pmid}" for pmid in pmids[:20]])

        return references
