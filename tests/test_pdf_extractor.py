"""Tests for PDF extractor and adapter.

Per RP7, this tests the PDF→pages→SourceDocument→EvidenceStore pipeline.
"""
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.evidence import EvidenceStore
from jarvis_core.pdf_extractor import (
    extract_pdf_pages,
    ingest_pdf,
    load_pdf_as_documents,
)
from jarvis_core.sources import ExecutionContext, ingest

SAMPLE_PDF = ROOT / "tests" / "fixtures" / "sample.pdf"


class TestExtractPdfPages:
    """Tests for extract_pdf_pages function."""

    def test_extract_returns_correct_page_count(self):
        """Should return one entry per page."""
        pages = extract_pdf_pages(SAMPLE_PDF)
        assert len(pages) == 3

    def test_each_page_has_page_and_text(self):
        """Each entry should have page number and text."""
        pages = extract_pdf_pages(SAMPLE_PDF)
        for page in pages:
            assert "page" in page
            assert "text" in page
            assert isinstance(page["page"], int)
            assert isinstance(page["text"], str)

    def test_page_numbers_are_1_indexed(self):
        """Page numbers should start from 1."""
        pages = extract_pdf_pages(SAMPLE_PDF)
        page_nums = [p["page"] for p in pages]
        assert page_nums == [1, 2, 3]

    def test_pages_contain_text(self):
        """Sample PDF pages should contain expected text."""
        pages = extract_pdf_pages(SAMPLE_PDF)
        assert "Page 1" in pages[0]["text"]
        assert "Page 2" in pages[1]["text"]
        assert "Page 3" in pages[2]["text"]

    def test_nonexistent_file_raises_error(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            extract_pdf_pages("nonexistent.pdf")


class TestLoadPdfAsDocuments:
    """Tests for load_pdf_as_documents function."""

    def test_returns_source_documents(self):
        """Should return SourceDocument instances."""
        docs = load_pdf_as_documents(SAMPLE_PDF)
        assert len(docs) == 3
        for doc in docs:
            assert doc.source == "pdf"

    def test_locator_base_includes_page(self):
        """locator_base should include page number."""
        docs = load_pdf_as_documents(SAMPLE_PDF)
        assert "#page:1" in docs[0].locator_base
        assert "#page:2" in docs[1].locator_base
        assert "#page:3" in docs[2].locator_base

    def test_metadata_includes_page_info(self):
        """Metadata should include page and total_pages."""
        docs = load_pdf_as_documents(SAMPLE_PDF)
        for i, doc in enumerate(docs):
            assert doc.metadata["page"] == i + 1
            assert doc.metadata["total_pages"] == 3


class TestIngestPdf:
    """Tests for ingest_pdf convenience function."""

    def test_ingest_creates_chunks(self):
        """ingest_pdf should create chunks in EvidenceStore."""
        store = EvidenceStore()
        results = ingest_pdf(SAMPLE_PDF, store)

        assert len(results) > 0
        for result in results:
            assert store.has_chunk(result.chunk_id)

    def test_ingest_locator_format(self):
        """Chunk locators should have page and chunk info."""
        store = EvidenceStore()
        results = ingest_pdf(SAMPLE_PDF, store)

        for result in results:
            assert "#page:" in result.locator
            assert "#chunk:" in result.locator

    def test_ingest_preview_includes_page(self):
        """Previews should include page number."""
        store = EvidenceStore()
        results = ingest_pdf(SAMPLE_PDF, store)

        # At least some previews should include page info
        assert any("[p." in r.preview for r in results)

    def test_ingest_adds_to_context(self):
        """ingest_pdf should add chunks to ExecutionContext."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        results = ingest_pdf(SAMPLE_PDF, store, context=ctx)

        assert len(ctx.available_chunks) == len(results)
        for result in results:
            assert result.chunk_id in ctx.get_chunk_ids()


class TestIntegration:
    """Integration tests for full PDF pipeline."""

    def test_pdf_to_evidence_store_pipeline(self):
        """Full pipeline: PDF→pages→docs→chunks→EvidenceStore."""
        store = EvidenceStore()
        ctx = ExecutionContext(evidence_store=store)

        # Load PDF
        docs = load_pdf_as_documents(SAMPLE_PDF)

        # Ingest each page document
        all_results = []
        for doc in docs:
            results = ingest(doc, store)
            all_results.extend(results)
            ctx.add_chunks(results)

        # Verify all chunks are accessible
        for result in all_results:
            chunk = store.get_chunk(result.chunk_id)
            assert chunk is not None
            assert "#page:" in chunk.locator

        # Verify context has all chunks
        assert len(ctx.get_chunk_ids()) == len(all_results)

    def test_chunk_quote_from_pdf_content(self):
        """Quotes should contain actual PDF content."""
        store = EvidenceStore()
        results = ingest_pdf(SAMPLE_PDF, store)

        # At least one chunk should have content from the PDF
        all_quotes = [store.get_quote(r.chunk_id) for r in results]
        assert any("Page" in q for q in all_quotes)
