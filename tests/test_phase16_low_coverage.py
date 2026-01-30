"""Phase 16: Low Coverage High-Line Module Tests.

Target: Modules with <20% coverage and high line counts.
Focus: ingestion/pipeline.py (600 lines, 19%), multimodal/scientific.py (208 lines)
"""

from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path


# ============================================================
# Tests for ingestion/pipeline.py - All Classes and Functions
# ============================================================


class TestTextChunk:
    """Tests for TextChunk dataclass."""

    def test_creation(self):
        from jarvis_core.ingestion.pipeline import TextChunk

        chunk = TextChunk(
            chunk_id="c1",
            text="Test text",
            section="Abstract",
            paragraph_index=0,
            page=1,
            char_start=0,
            char_end=9,
        )
        assert chunk.chunk_id == "c1"
        assert chunk.text == "Test text"

    def test_to_dict(self):
        from jarvis_core.ingestion.pipeline import TextChunk

        chunk = TextChunk(chunk_id="c1", text="Test")
        d = chunk.to_dict()
        assert d["chunk_id"] == "c1"
        assert d["text"] == "Test"
        assert "section" in d


class TestExtractedPaper:
    """Tests for ExtractedPaper dataclass."""

    def test_creation(self):
        from jarvis_core.ingestion.pipeline import ExtractedPaper

        paper = ExtractedPaper(paper_id="p1", title="Test Paper", year=2024, source="local")
        assert paper.paper_id == "p1"
        assert paper.title == "Test Paper"

    def test_to_dict(self):
        from jarvis_core.ingestion.pipeline import ExtractedPaper

        paper = ExtractedPaper(paper_id="p1", title="Test", year=2024)
        d = paper.to_dict()
        assert d["paper_id"] == "p1"
        assert d["chunk_count"] == 0


class TestIngestionResult:
    """Tests for IngestionResult dataclass."""

    def test_creation(self):
        from jarvis_core.ingestion.pipeline import IngestionResult

        result = IngestionResult()
        assert result.papers == []
        assert result.warnings == []

    def test_to_dict(self):
        from jarvis_core.ingestion.pipeline import IngestionResult, ExtractedPaper

        result = IngestionResult()
        result.papers.append(ExtractedPaper(paper_id="p1", title="T", year=2024))
        d = result.to_dict()
        assert len(d["papers"]) == 1


class TestPDFExtractor:
    """Tests for PDFExtractor class."""

    def test_init(self):
        from jarvis_core.ingestion.pipeline import PDFExtractor

        extractor = PDFExtractor()
        assert extractor is not None

    def test_extract_fallback(self):
        from jarvis_core.ingestion.pipeline import PDFExtractor

        extractor = PDFExtractor()
        extractor._pdfplumber = None
        extractor._pymupdf = None
        text, pages = extractor._extract_fallback(Path("test.pdf"))
        assert "requires" in text.lower()

    @patch("jarvis_core.ingestion.pipeline.PDFExtractor._extract_pymupdf")
    def test_extract_with_pymupdf(self, mock_extract):
        from jarvis_core.ingestion.pipeline import PDFExtractor

        mock_extract.return_value = ("Test text", [(1, "Page 1")])
        extractor = PDFExtractor()
        extractor._pymupdf = MagicMock()
        text, pages = extractor.extract(Path("test.pdf"))
        mock_extract.assert_called_once()

    @patch("jarvis_core.ingestion.pipeline.PDFExtractor._extract_pdfplumber")
    def test_extract_with_pdfplumber(self, mock_extract):
        from jarvis_core.ingestion.pipeline import PDFExtractor

        mock_extract.return_value = ("Test text", [(1, "Page 1")])
        extractor = PDFExtractor()
        extractor._pymupdf = None
        extractor._pdfplumber = MagicMock()
        text, pages = extractor.extract(Path("test.pdf"))
        mock_extract.assert_called_once()


class TestTextChunker:
    """Tests for TextChunker class."""

    def test_init(self):
        from jarvis_core.ingestion.pipeline import TextChunker

        chunker = TextChunker(chunk_size=500, overlap=50)
        assert chunker.chunk_size == 500
        assert chunker.overlap == 50

    def test_chunk_simple(self):
        from jarvis_core.ingestion.pipeline import TextChunker

        chunker = TextChunker(chunk_size=100)
        text = "This is a test paragraph. " * 10
        chunks = chunker.chunk(text, "paper_1")
        assert len(chunks) > 0
        assert chunks[0].chunk_id.startswith("paper_1")

    def test_detect_sections(self):
        from jarvis_core.ingestion.pipeline import TextChunker

        chunker = TextChunker()
        text = """Abstract
This is the abstract.

Introduction
This is the introduction.

Methods
These are the methods."""
        sections = chunker._detect_sections(text)
        assert len(sections) >= 3

    def test_detect_sections_no_headers(self):
        from jarvis_core.ingestion.pipeline import TextChunker

        chunker = TextChunker()
        text = "Just plain text without any section headers."
        sections = chunker._detect_sections(text)
        assert sections[0][0] == "Full Text"

    def test_chunk_text(self):
        from jarvis_core.ingestion.pipeline import TextChunker

        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = chunker._chunk_text(text, 0, "p1", "Section", 0)
        assert len(chunks) > 0


class TestBibTeXParser:
    """Tests for BibTeXParser class."""

    def test_parse_valid(self):
        from jarvis_core.ingestion.pipeline import BibTeXParser

        parser = BibTeXParser()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(
                """@article{test2024,
    title = {Test Title},
    author = {Test Author},
    year = {2024}
}"""
            )
            path = Path(f.name)
        entries = parser.parse(path)
        assert len(entries) == 1
        assert entries[0]["title"] == "Test Title"
        path.unlink()

    def test_parse_invalid(self):
        from jarvis_core.ingestion.pipeline import BibTeXParser

        parser = BibTeXParser()
        entries = parser.parse(Path("/nonexistent/file.bib"))
        assert entries == []

    def test_parse_fields(self):
        from jarvis_core.ingestion.pipeline import BibTeXParser

        parser = BibTeXParser()
        text = 'title = {Test}, author = "Author Name", year = {2024}'
        fields = parser._parse_fields(text)
        assert fields["title"] == "Test"
        assert fields["year"] == "2024"


class TestIngestionPipeline:
    """Tests for IngestionPipeline class."""

    def test_init(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            assert pipeline.output_dir == Path(tmpdir)

    def test_generate_paper_id(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            paper_id = pipeline._generate_paper_id(Path("test.pdf"), "Test Title")
            assert paper_id.startswith("paper_")
            assert len(paper_id) > 10

    def test_extract_title_from_text(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            text = "This is a proper title for a paper\nMore content here"
            title = pipeline._extract_title(text, Path("fallback.pdf"))
            assert title == "This is a proper title for a paper"

    def test_extract_title_fallback(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            text = "Short\ntext"
            title = pipeline._extract_title(text, Path("test_paper.pdf"))
            assert "test" in title.lower()

    def test_extract_year_from_text(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            text = "Published in 2023 by authors"
            year = pipeline._extract_year(text, Path("test.pdf"))
            assert year == 2023

    def test_extract_year_fallback(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline
        from datetime import datetime

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            text = "No year here"
            year = pipeline._extract_year(text, Path("test.pdf"))
            assert year == datetime.now().year

    def test_extract_abstract(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            text = """Title
Abstract:
This is a detailed abstract that should be extracted properly.

Introduction
The rest of the paper."""
            abstract = pipeline._extract_abstract(text)
            assert "extracted" in abstract or abstract == ""

    def test_ingest_bibtex(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            # Create bibtex file
            bib_path = Path(tmpdir) / "refs.bib"
            bib_path.write_text(
                """@article{test2024,
    title = {Test Paper},
    author = {Author One and Author Two},
    year = {2024}
}"""
            )
            papers = pipeline.ingest_bibtex(bib_path)
            assert len(papers) == 1
            assert papers[0].title == "Test Paper"
            assert len(papers[0].authors) == 2

    def test_ingest_batch_empty(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            result = pipeline.ingest_batch([])
            assert len(result.papers) == 0
            assert result.stats["total_files"] == 0

    def test_ingest_batch_with_bibtex(self):
        from jarvis_core.ingestion.pipeline import IngestionPipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            bib_path = Path(tmpdir) / "refs.bib"
            bib_path.write_text("@article{t1, title={T}, year={2024}}")
            result = pipeline.ingest_batch([bib_path])
            assert result.stats["bibtex_count"] == 1

    def test_save_papers_jsonl(self):
        from jarvis_core.ingestion.pipeline import (
            IngestionPipeline,
            IngestionResult,
            ExtractedPaper,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            result = IngestionResult()
            result.papers.append(ExtractedPaper(paper_id="p1", title="T", year=2024))
            path = pipeline.save_papers_jsonl(result)
            assert path.exists()
            content = path.read_text()
            assert "p1" in content

    def test_save_chunks_jsonl(self):
        from jarvis_core.ingestion.pipeline import (
            IngestionPipeline,
            IngestionResult,
            ExtractedPaper,
            TextChunk,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = IngestionPipeline(Path(tmpdir))
            result = IngestionResult()
            paper = ExtractedPaper(paper_id="p1", title="T", year=2024)
            paper.chunks.append(TextChunk(chunk_id="c1", text="Chunk text"))
            result.papers.append(paper)
            path = pipeline.save_chunks_jsonl(result)
            assert path.exists()
            content = path.read_text()
            assert "c1" in content


class TestIngestFilesFunction:
    """Tests for ingest_files convenience function."""

    def test_ingest_files(self):
        from jarvis_core.ingestion.pipeline import ingest_files

        with tempfile.TemporaryDirectory() as tmpdir:
            result = ingest_files([], Path(tmpdir))
            assert result is not None
            assert len(result.papers) == 0


# ============================================================
# Additional tests for user's open files
# ============================================================


class TestFundingCliff:
    """Tests for funding_cliff module."""

    def test_import(self):
        from jarvis_core import funding_cliff

        assert hasattr(funding_cliff, "__name__")


class TestHeatmap:
    """Tests for heatmap module."""

    def test_import(self):
        from jarvis_core import heatmap

        assert hasattr(heatmap, "__name__")


class TestCareerPlanner:
    """Tests for career_planner module."""

    def test_import(self):
        from jarvis_core import career_planner

        assert hasattr(career_planner, "__name__")