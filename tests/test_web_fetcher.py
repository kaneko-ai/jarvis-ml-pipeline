"""Tests for Web Fetcher and HTML extractor.

Per RP8, these tests use mocks to avoid network dependencies.
"""
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.evidence import EvidenceStore
from jarvis_core.html_extractor import extract_main_text, extract_title
from jarvis_core.sources import ExecutionContext
from jarvis_core.web_fetcher import (
    FetchError,
    FetchMeta,
    fetch_url,
    ingest_url,
    load_url_as_document,
)


class TestExtractMainText:
    """Tests for HTML text extraction."""

    def test_removes_script_tags(self):
        """Should remove script content."""
        html = "<html><body><script>alert('x');</script>Hello World</body></html>"
        text = extract_main_text(html)
        assert "alert" not in text
        assert "Hello World" in text

    def test_removes_style_tags(self):
        """Should remove style content."""
        html = "<html><body><style>.x{color:red}</style>Hello World</body></html>"
        text = extract_main_text(html)
        assert "color" not in text
        assert "Hello World" in text

    def test_prefers_article_tag(self):
        """Should prefer <article> content."""
        html = """
        <html><body>
            <nav>Navigation</nav>
            <article>Article Content Here</article>
            <footer>Footer</footer>
        </body></html>
        """
        text = extract_main_text(html)
        assert "Article Content" in text
        # nav/footer might be removed

    def test_prefers_main_tag(self):
        """Should prefer <main> content when no article."""
        html = """
        <html><body>
            <header>Header</header>
            <main>Main Content Here</main>
            <footer>Footer</footer>
        </body></html>
        """
        text = extract_main_text(html)
        assert "Main Content" in text

    def test_normalizes_whitespace(self):
        """Should normalize excessive whitespace."""
        html = "<html><body>Hello     World\n\n\n\nTest</body></html>"
        text = extract_main_text(html)
        assert "     " not in text  # No excessive spaces


class TestExtractTitle:
    """Tests for title extraction."""

    def test_extracts_title(self):
        """Should extract page title."""
        html = "<html><head><title>My Page Title</title></head><body></body></html>"
        title = extract_title(html)
        assert title == "My Page Title"

    def test_returns_none_when_no_title(self):
        """Should return None when no title tag."""
        html = "<html><head></head><body>Hello</body></html>"
        title = extract_title(html)
        assert title is None


class TestFetchUrl:
    """Tests for URL fetching (mocked)."""

    def test_fetch_returns_html_and_meta(self):
        """Should return HTML content and metadata."""
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>Hello</body></html>"
            mock_response.url = "https://example.com/page"
            mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
            mock_get.return_value = mock_response

            html, meta = fetch_url("https://example.com/page")

            assert "Hello" in html
            assert meta.status_code == 200
            assert meta.final_url == "https://example.com/page"
            assert "text/html" in meta.content_type

    def test_fetch_handles_redirect(self):
        """Should capture final URL after redirect."""
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>Content</body></html>"
            mock_response.url = "https://example.com/redirected"  # After redirect
            mock_response.headers = {"Content-Type": "text/html"}
            mock_get.return_value = mock_response

            _, meta = fetch_url("https://example.com/original")

            assert meta.final_url == "https://example.com/redirected"

    def test_fetch_detects_pdf(self):
        """Should detect PDF content type."""
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_response.url = "https://example.com/doc.pdf"
            mock_response.headers = {"Content-Type": "application/pdf"}
            mock_get.return_value = mock_response

            html, meta = fetch_url("https://example.com/doc.pdf")

            assert meta.is_pdf is True
            assert html == ""

    def test_fetch_rejects_unsupported_content_type(self):
        """Should raise error for unsupported content types."""
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com/data.json"
            mock_response.headers = {"Content-Type": "application/json"}
            mock_get.return_value = mock_response

            with pytest.raises(FetchError, match="Unsupported content type"):
                fetch_url("https://example.com/data.json")


class TestLoadUrlAsDocument:
    """Tests for URL to SourceDocument conversion."""

    def test_creates_source_document(self):
        """Should create SourceDocument with correct attributes."""
        html = "<html><head><title>Test Page</title></head><body>Content</body></html>"
        meta = FetchMeta(
            final_url="https://example.com/page",
            status_code=200,
            content_type="text/html",
            is_pdf=False,
        )

        doc = load_url_as_document("https://example.com", html=html, meta=meta)

        assert doc.source == "url"
        assert "url:https://example.com/page" in doc.locator_base
        assert "Content" in doc.text
        assert doc.metadata["title"] == "Test Page"

    def test_raises_for_pdf_content(self):
        """Should raise if content is PDF."""
        meta = FetchMeta(
            final_url="https://example.com/doc.pdf",
            status_code=200,
            content_type="application/pdf",
            is_pdf=True,
        )

        with pytest.raises(FetchError, match="PDF"):
            load_url_as_document("https://example.com/doc.pdf", html="", meta=meta)


class TestIngestUrl:
    """Tests for URL ingestion into EvidenceStore."""

    def test_ingest_creates_chunks(self):
        """Should create chunks in EvidenceStore."""
        with patch("jarvis_core.web_fetcher.fetch_url") as mock_fetch:
            mock_fetch.return_value = (
                "<html><body>Test content for chunking</body></html>",
                FetchMeta(
                    final_url="https://example.com/page",
                    status_code=200,
                    content_type="text/html",
                    is_pdf=False,
                ),
            )

            store = EvidenceStore()
            results = ingest_url("https://example.com/page", store)

            assert len(results) > 0
            for result in results:
                assert store.has_chunk(result.chunk_id)

    def test_ingest_locator_format(self):
        """Chunk locators should have URL and chunk info."""
        with patch("jarvis_core.web_fetcher.fetch_url") as mock_fetch:
            mock_fetch.return_value = (
                "<html><body>Content</body></html>",
                FetchMeta(
                    final_url="https://example.com/page",
                    status_code=200,
                    content_type="text/html",
                    is_pdf=False,
                ),
            )

            store = EvidenceStore()
            results = ingest_url("https://example.com/page", store)

            for result in results:
                assert "url:https://example.com/page" in result.locator
                assert "#chunk:" in result.locator

    def test_ingest_adds_to_context(self):
        """Should add chunks to ExecutionContext."""
        with patch("jarvis_core.web_fetcher.fetch_url") as mock_fetch:
            mock_fetch.return_value = (
                "<html><body>Content</body></html>",
                FetchMeta(
                    final_url="https://example.com/page",
                    status_code=200,
                    content_type="text/html",
                    is_pdf=False,
                ),
            )

            store = EvidenceStore()
            ctx = ExecutionContext(evidence_store=store)
            results = ingest_url("https://example.com/page", store, context=ctx)

            assert len(ctx.available_chunks) == len(results)

    def test_ingest_raises_for_pdf_url(self):
        """Should raise when URL returns PDF."""
        with patch("jarvis_core.web_fetcher.fetch_url") as mock_fetch:
            mock_fetch.return_value = (
                "",
                FetchMeta(
                    final_url="https://example.com/doc.pdf",
                    status_code=200,
                    content_type="application/pdf",
                    is_pdf=True,
                ),
            )

            store = EvidenceStore()
            with pytest.raises(FetchError, match="PDF"):
                ingest_url("https://example.com/doc.pdf", store)
