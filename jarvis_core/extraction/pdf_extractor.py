"""
JARVIS PDF Extractor

1. PDF全文抽出: 論文PDFから構造化テキストを抽出
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PDFSection:
    """PDFセクション."""
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
    """抽出済みPDFドキュメント."""
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
        """全文を取得."""
        parts = [self.abstract]
        for section in self.sections:
            parts.append(f"\n## {section.title}\n{section.content}")
        return "\n".join(parts)


class PDFExtractor:
    """PDF抽出器.
    
    PyMuPDF (fitz) を使用してPDFからテキストを抽出
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
        """初期化."""
        self._fitz = None

    def _get_fitz(self):
        """PyMuPDFを遅延ロード."""
        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                logger.warning("PyMuPDF not installed. Install with: pip install pymupdf")
                self._fitz = None
        return self._fitz

    def extract(self, pdf_path: str) -> PDFDocument:
        """PDFからテキストを抽出.
        
        Args:
            pdf_path: PDFファイルパス
        
        Returns:
            抽出済みドキュメント
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        fitz = self._get_fitz()

        if fitz is None:
            # Fallback: 基本的なテキスト抽出
            return self._extract_fallback(pdf_path)

        return self._extract_with_fitz(pdf_path, fitz)

    def _extract_with_fitz(self, pdf_path: str, fitz) -> PDFDocument:
        """PyMuPDFで抽出."""
        doc = fitz.open(pdf_path)

        # メタデータ
        metadata = doc.metadata
        title = metadata.get("title", "") or Path(pdf_path).stem
        authors = metadata.get("author", "").split(",")

        # 全ページのテキスト
        full_text = ""
        page_texts = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            page_texts.append((page_num + 1, text))
            full_text += text + "\n"

        doc.close()

        # セクション分割
        sections = self._parse_sections(page_texts)

        # Abstract抽出
        abstract = ""
        for section in sections:
            if section.section_type == "abstract":
                abstract = section.content
                break

        # 参考文献抽出
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
        """フォールバック抽出（PyMuPDFなし）."""
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
        """セクションを分割."""
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

                # セクションヘッダーを検出
                section_type = self._detect_section_type(line)

                if section_type:
                    # 前のセクションを保存
                    if current_section:
                        sections.append(PDFSection(
                            title=current_section,
                            content="\n".join(current_content),
                            page=current_page,
                            section_type=self._get_section_type(current_section),
                        ))

                    current_section = line
                    current_content = []
                    current_page = page_num
                else:
                    current_content.append(line)

        # 最後のセクション
        if current_section:
            sections.append(PDFSection(
                title=current_section,
                content="\n".join(current_content),
                page=current_page,
                section_type=self._get_section_type(current_section),
            ))

        return sections

    def _detect_section_type(self, line: str) -> str | None:
        """セクションタイプを検出."""
        for section_type, pattern in self.SECTION_PATTERNS.items():
            if re.match(pattern, line):
                return section_type
        return None

    def _get_section_type(self, title: str) -> str:
        """タイトルからセクションタイプを取得."""
        for section_type, pattern in self.SECTION_PATTERNS.items():
            if re.match(pattern, title):
                return section_type
        return "other"

    def _extract_references(self, text: str) -> list[str]:
        """参考文献を抽出."""
        references = []

        # DOIパターン
        dois = re.findall(r"10\.\d{4,}/[^\s]+", text)
        references.extend([f"DOI: {doi}" for doi in dois[:20]])

        # PMIDパターン
        pmids = re.findall(r"PMID[:\s]*(\d+)", text, re.IGNORECASE)
        references.extend([f"PMID: {pmid}" for pmid in pmids[:20]])

        return references
