"""Ingestion Pipeline (AG-08).

PDF/BibTeX/ZIPからpapers.jsonlを生成する取り込みパイプライン。
- PDF→テキスト抽出
- テキスト→チャンク化
- チャンク→locator付与
- papers.jsonl生成
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TextChunk:
    """テキストチャンク."""
    chunk_id: str
    text: str
    section: str = ""
    paragraph_index: int = 0
    page: int | None = None
    char_start: int = 0
    char_end: int = 0

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "section": self.section,
            "paragraph_index": self.paragraph_index,
            "page": self.page,
            "char_start": self.char_start,
            "char_end": self.char_end,
        }


@dataclass
class ExtractedPaper:
    """抽出された論文."""
    paper_id: str
    title: str
    year: int
    source: str = "local"  # local, pubmed, pmc
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    doi: str = ""
    pmid: str = ""
    filepath: str = ""
    chunks: list[TextChunk] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "year": self.year,
            "source": self.source,
            "abstract": self.abstract,
            "authors": self.authors,
            "doi": self.doi,
            "pmid": self.pmid,
            "filepath": self.filepath,
            "chunk_count": len(self.chunks),
        }


@dataclass
class IngestionResult:
    """取り込み結果."""
    papers: list[ExtractedPaper] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "papers": [p.to_dict() for p in self.papers],
            "warnings": self.warnings,
            "stats": self.stats,
        }


class PDFExtractor:
    """PDFテキスト抽出器."""

    def __init__(self):
        self._pdfplumber = None
        self._pymupdf = None
        self._init_backends()

    def _init_backends(self):
        """利用可能なバックエンドを初期化."""
        try:
            import pdfplumber
            self._pdfplumber = pdfplumber
        except ImportError:
            pass

        try:
            import fitz  # PyMuPDF
            self._pymupdf = fitz
        except ImportError:
            pass

    def extract(self, filepath: Path) -> tuple[str, list[tuple[int, str]]]:
        """PDFからテキストを抽出.
        
        Returns:
            (全テキスト, [(ページ番号, ページテキスト), ...])
        """
        if self._pymupdf:
            return self._extract_pymupdf(filepath)
        elif self._pdfplumber:
            return self._extract_pdfplumber(filepath)
        else:
            return self._extract_fallback(filepath)

    def _extract_pymupdf(self, filepath: Path) -> tuple[str, list[tuple[int, str]]]:
        """PyMuPDFでテキスト抽出."""
        pages = []
        all_text = []

        try:
            doc = self._pymupdf.open(filepath)
            for i, page in enumerate(doc):
                text = page.get_text()
                pages.append((i + 1, text))
                all_text.append(text)
            doc.close()
        except Exception as e:
            return f"[Error extracting PDF: {e}]", []

        return "\n\n".join(all_text), pages

    def _extract_pdfplumber(self, filepath: Path) -> tuple[str, list[tuple[int, str]]]:
        """pdfplumberでテキスト抽出."""
        pages = []
        all_text = []

        try:
            with self._pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages.append((i + 1, text))
                    all_text.append(text)
        except Exception as e:
            return f"[Error extracting PDF: {e}]", []

        return "\n\n".join(all_text), pages

    def _extract_fallback(self, filepath: Path) -> tuple[str, list[tuple[int, str]]]:
        """フォールバック（PDFライブラリなし）."""
        return "[PDF extraction requires pdfplumber or PyMuPDF]", []


class TextChunker:
    """テキストチャンク化器."""

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 100,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(
        self,
        text: str,
        paper_id: str,
        pages: list[tuple[int, str]] | None = None,
    ) -> list[TextChunk]:
        """テキストをチャンク化.
        
        Args:
            text: 全テキスト
            paper_id: 論文ID
            pages: ページ情報（オプション）
            
        Returns:
            チャンクリスト
        """
        chunks = []

        # セクション検出
        sections = self._detect_sections(text)

        chunk_id = 0
        for section_name, section_text, section_start in sections:
            # セクション内をチャンク化
            section_chunks = self._chunk_text(
                section_text,
                section_start,
                paper_id,
                section_name,
                chunk_id,
            )
            chunks.extend(section_chunks)
            chunk_id += len(section_chunks)

        return chunks

    def _detect_sections(self, text: str) -> list[tuple[str, str, int]]:
        """セクションを検出.
        
        Returns:
            [(セクション名, セクションテキスト, 開始位置), ...]
        """
        # よくあるセクションヘッダーのパターン
        section_patterns = [
            r"^(Abstract|ABSTRACT)[\s:]*$",
            r"^(Introduction|INTRODUCTION)[\s:]*$",
            r"^(Methods?|METHODS?|Materials? and Methods?)[\s:]*$",
            r"^(Results?|RESULTS?)[\s:]*$",
            r"^(Discussion|DISCUSSION)[\s:]*$",
            r"^(Conclusion|CONCLUSION|Conclusions?)[\s:]*$",
            r"^(References?|REFERENCES?)[\s:]*$",
            r"^\d+\.\s*([A-Z][a-z]+.*)$",  # 番号付きセクション
        ]

        combined_pattern = "|".join(f"({p})" for p in section_patterns)

        sections = []
        current_section = "Unknown"
        current_start = 0
        current_text = []

        lines = text.split("\n")
        char_pos = 0

        for line in lines:
            # セクションヘッダーかチェック
            if re.match(combined_pattern, line.strip(), re.MULTILINE):
                # 前のセクションを保存
                if current_text:
                    sections.append((
                        current_section,
                        "\n".join(current_text),
                        current_start,
                    ))

                # 新しいセクション開始
                current_section = line.strip()
                current_start = char_pos
                current_text = []
            else:
                current_text.append(line)

            char_pos += len(line) + 1

        # 最後のセクション
        if current_text:
            sections.append((
                current_section,
                "\n".join(current_text),
                current_start,
            ))

        # セクションが検出されなかった場合は全体を1セクションに
        if not sections:
            sections = [("Full Text", text, 0)]

        return sections

    def _chunk_text(
        self,
        text: str,
        base_offset: int,
        paper_id: str,
        section: str,
        start_chunk_id: int,
    ) -> list[TextChunk]:
        """テキストをチャンク化."""
        chunks = []

        # 段落で分割
        paragraphs = re.split(r'\n\s*\n', text)

        current_chunk = []
        current_len = 0
        char_pos = 0
        para_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current_len + len(para) > self.chunk_size and current_chunk:
                # 現在のチャンクを保存
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(TextChunk(
                    chunk_id=f"{paper_id}_chunk_{start_chunk_id + len(chunks)}",
                    text=chunk_text,
                    section=section,
                    paragraph_index=para_idx - len(current_chunk),
                    char_start=base_offset + char_pos - len(chunk_text),
                    char_end=base_offset + char_pos,
                ))

                # オーバーラップ分を残して新規チャンク
                if self.overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1]]
                    current_len = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_len = 0

            current_chunk.append(para)
            current_len += len(para)
            char_pos += len(para) + 2
            para_idx += 1

        # 残りを保存
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(TextChunk(
                chunk_id=f"{paper_id}_chunk_{start_chunk_id + len(chunks)}",
                text=chunk_text,
                section=section,
                paragraph_index=para_idx - len(current_chunk),
                char_start=base_offset + char_pos - len(chunk_text),
                char_end=base_offset + char_pos,
            ))

        return chunks


class BibTeXParser:
    """BibTeXファイルパーサー."""

    def parse(self, filepath: Path) -> list[dict[str, Any]]:
        """BibTeXファイルをパース."""
        entries = []

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
        except:
            return []

        # エントリを抽出
        entry_pattern = r'@(\w+)\s*\{([^,]+),\s*([^@]*)\}'

        for match in re.finditer(entry_pattern, content, re.DOTALL):
            entry_type = match.group(1).lower()
            cite_key = match.group(2).strip()
            fields_text = match.group(3)

            fields = self._parse_fields(fields_text)
            fields["entry_type"] = entry_type
            fields["cite_key"] = cite_key

            entries.append(fields)

        return entries

    def _parse_fields(self, text: str) -> dict[str, str]:
        """フィールドをパース."""
        fields = {}

        # field = {value} または field = "value"
        field_pattern = r'(\w+)\s*=\s*[{"]([^}"]*)[}"]'

        for match in re.finditer(field_pattern, text):
            key = match.group(1).lower()
            value = match.group(2).strip()
            fields[key] = value

        return fields


class IngestionPipeline:
    """取り込みパイプライン.
    
    PDF/BibTeX/ZIPからpapers.jsonlを生成。
    """

    def __init__(
        self,
        output_dir: Path,
        chunk_size: int = 1000,
    ):
        self.output_dir = output_dir
        self.pdf_extractor = PDFExtractor()
        self.chunker = TextChunker(chunk_size=chunk_size)
        self.bibtex_parser = BibTeXParser()

    def ingest_pdf(self, filepath: Path) -> ExtractedPaper:
        """単一PDFを取り込み."""
        # PDFからテキスト抽出
        text, pages = self.pdf_extractor.extract(filepath)

        # メタデータ推測
        title = self._extract_title(text, filepath)
        year = self._extract_year(text, filepath)

        # paper_id生成
        paper_id = self._generate_paper_id(filepath, title)

        # チャンク化
        chunks = self.chunker.chunk(text, paper_id, pages)

        return ExtractedPaper(
            paper_id=paper_id,
            title=title,
            year=year,
            source="local",
            abstract=self._extract_abstract(text),
            filepath=str(filepath),
            chunks=chunks,
        )

    def ingest_bibtex(self, filepath: Path) -> list[ExtractedPaper]:
        """BibTeXファイルを取り込み."""
        entries = self.bibtex_parser.parse(filepath)
        papers = []

        for entry in entries:
            paper_id = entry.get("cite_key", "")
            if not paper_id:
                continue

            year_str = entry.get("year", "0")
            try:
                year = int(year_str)
            except:
                year = 0

            papers.append(ExtractedPaper(
                paper_id=paper_id,
                title=entry.get("title", ""),
                year=year,
                source="bibtex",
                abstract=entry.get("abstract", ""),
                authors=entry.get("author", "").split(" and "),
                doi=entry.get("doi", ""),
            ))

        return papers

    def ingest_batch(
        self,
        filepaths: list[Path],
    ) -> IngestionResult:
        """複数ファイルをバッチ取り込み.
        
        Args:
            filepaths: ファイルパスリスト
            
        Returns:
            IngestionResult
        """
        result = IngestionResult()
        result.stats = {
            "total_files": len(filepaths),
            "pdf_count": 0,
            "bibtex_count": 0,
            "success_count": 0,
            "error_count": 0,
        }

        for filepath in filepaths:
            try:
                if filepath.suffix.lower() == ".pdf":
                    paper = self.ingest_pdf(filepath)
                    result.papers.append(paper)
                    result.stats["pdf_count"] += 1
                    result.stats["success_count"] += 1

                elif filepath.suffix.lower() == ".bib":
                    papers = self.ingest_bibtex(filepath)
                    result.papers.extend(papers)
                    result.stats["bibtex_count"] += 1
                    result.stats["success_count"] += len(papers)

            except Exception as e:
                result.warnings.append({
                    "code": "INGEST_ERROR",
                    "message": str(e),
                    "file": str(filepath),
                })
                result.stats["error_count"] += 1

        return result

    def save_papers_jsonl(
        self,
        result: IngestionResult,
        filepath: Path | None = None,
    ) -> Path:
        """papers.jsonlを保存."""
        if filepath is None:
            filepath = self.output_dir / "papers.jsonl"

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            for paper in result.papers:
                f.write(json.dumps(paper.to_dict(), ensure_ascii=False) + "\n")

        return filepath

    def save_chunks_jsonl(
        self,
        result: IngestionResult,
        filepath: Path | None = None,
    ) -> Path:
        """chunks.jsonlを保存（検索用）."""
        if filepath is None:
            filepath = self.output_dir / "chunks.jsonl"

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            for paper in result.papers:
                for chunk in paper.chunks:
                    chunk_data = chunk.to_dict()
                    chunk_data["paper_id"] = paper.paper_id
                    chunk_data["paper_title"] = paper.title
                    f.write(json.dumps(chunk_data, ensure_ascii=False) + "\n")

        return filepath

    def _generate_paper_id(self, filepath: Path, title: str) -> str:
        """paper_idを生成."""
        # ファイル名 + タイトルのハッシュ
        source = f"{filepath.name}:{title}"
        hash_val = hashlib.sha256(source.encode()).hexdigest()[:12]
        return f"paper_{hash_val}"

    def _extract_title(self, text: str, filepath: Path) -> str:
        """タイトルを抽出."""
        # 最初の行がタイトルっぽければ使用
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            first_line = lines[0]
            if 10 < len(first_line) < 200:
                return first_line

        # ファイル名からフォールバック
        return filepath.stem.replace("_", " ").replace("-", " ")

    def _extract_year(self, text: str, filepath: Path) -> int:
        """年を抽出."""
        # テキストから年を検索
        year_match = re.search(r'\b(19|20)\d{2}\b', text[:2000])
        if year_match:
            return int(year_match.group())

        return datetime.now().year

    def _extract_abstract(self, text: str) -> str:
        """アブストラクトを抽出."""
        # "Abstract"セクションを探す
        abstract_match = re.search(
            r'(?:Abstract|ABSTRACT)[:\s]*\n(.*?)(?:\n\n|\n[A-Z])',
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if abstract_match:
            abstract = abstract_match.group(1).strip()
            if len(abstract) > 50:
                return abstract[:2000]

        return ""


def ingest_files(
    filepaths: list[Path],
    output_dir: Path,
) -> IngestionResult:
    """便利関数: ファイルを取り込み."""
    pipeline = IngestionPipeline(output_dir)
    return pipeline.ingest_batch(filepaths)
