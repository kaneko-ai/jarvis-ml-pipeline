"""Golden Path Test for Ingestion (PR-3)."""

import json
from pathlib import Path
import pytest
from jarvis_core.ingestion.pipeline import (
    IngestionPipeline,
    TextChunker,
    BibTeXParser,
    PDFExtractor,
)


@pytest.fixture
def tmp_output_dir(tmp_path):
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def sample_bib(tmp_path):
    bib_path = tmp_path / "test.bib"
    bib_path.write_text(
        """
@article{test2026,
  author = {Jarvis, A. and Smith, B.},
  title = {A Great Research Paper},
  journal = {Journal of AI},
  year = {2026},
  abstract = {This is a sample abstract about AI research.},
  doi = {10.1000/test.2026}
}
""",
        encoding="utf-8",
    )
    return bib_path


@pytest.fixture
def sample_pdf():
    return Path("tests/fixtures/sample.pdf")


def test_text_chunker():
    chunker = TextChunker(chunk_size=100, overlap=10)
    text = "Introduction\nThis is the first paragraph. It should be long enough to test chunking.\n\nMethods\nThis is the second paragraph. We have multiple sections here to test section detection."
    chunks = chunker.chunk(text, "paper_1")

    assert len(chunks) >= 2
    assert any(c.section == "Introduction" for c in chunks)
    assert any(c.section == "Methods" for c in chunks)
    assert chunks[0].chunk_id.startswith("paper_1_chunk_")


def test_bibtex_parser(sample_bib):
    parser = BibTeXParser()
    entries = parser.parse(sample_bib)

    assert len(entries) == 1
    assert entries[0]["cite_key"] == "test2026"
    assert entries[0]["title"] == "A Great Research Paper"
    assert entries[0]["year"] == "2026"


def test_pdf_extractor(sample_pdf):
    if not sample_pdf.exists():
        pytest.skip("sample.pdf fixture not found")

    extractor = PDFExtractor()
    text, pages = extractor.extract(sample_pdf)

    # We generated 3 pages in scripts/generate_test_pdf.py
    assert len(pages) == 3
    assert "Page 1" in text
    assert "Page 2" in text
    assert "Page 3" in text


def test_ingestion_pipeline_batch(tmp_output_dir, sample_pdf, sample_bib):
    pipeline = IngestionPipeline(output_dir=tmp_output_dir, chunk_size=500)

    files = [sample_pdf, sample_bib]
    result = pipeline.ingest_batch(files)

    assert result.stats["pdf_count"] == 1
    assert result.stats["bibtex_count"] == 1
    assert result.stats["success_count"] >= 2
    assert len(result.papers) >= 2

    # Test saving
    papers_jsonl = pipeline.save_papers_jsonl(result)
    chunks_jsonl = pipeline.save_chunks_jsonl(result)

    assert papers_jsonl.exists()
    assert chunks_jsonl.exists()

    # Verify papers.jsonl content
    with open(papers_jsonl, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) >= 2
        paper_data = json.loads(lines[0])
        assert "paper_id" in paper_data


def test_ingestion_abstract_extraction():
    pipeline = IngestionPipeline(output_dir=Path("./tmp"))
    text = "Title of Paper\n\nAbstract\nThis is the abstract content that needs to be extracted correctly. It ends with double newline.\n\nIntroduction\n..."
    abstract = pipeline._extract_abstract(text)
    assert "is the abstract content" in abstract


def test_ingestion_year_extraction():
    pipeline = IngestionPipeline(output_dir=Path("./tmp"))
    assert pipeline._extract_year("Published in 2024.", Path("test.pdf")) == 2024
    assert (
        pipeline._extract_year("No year here.", Path("test.pdf")) == 2026
    )  # Current year in simulation is 2026