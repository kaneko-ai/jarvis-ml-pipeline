"""Comprehensive tests for web_fetcher module with mocking."""

from unittest.mock import patch, MagicMock, PropertyMock
import pytest
import requests

from jarvis_core.web_fetcher import (
    FetchMeta,
    FetchError,
    fetch_url,
    load_url_as_document,
    DEFAULT_USER_AGENT,
)


class TestFetchMeta:
    def test_creation(self):
        meta = FetchMeta(
            final_url="https://example.com",
            status_code=200,
            content_type="text/html",
        )
        
        assert meta.final_url == "https://example.com"
        assert meta.status_code == 200
        assert meta.is_pdf is False

    def test_pdf_detection(self):
        meta = FetchMeta(
            final_url="https://example.com/doc.pdf",
            status_code=200,
            content_type="application/pdf",
            is_pdf=True,
        )
        
        assert meta.is_pdf is True


class TestFetchError:
    def test_creation_with_status(self):
        error = FetchError("Not Found", status_code=404)
        
        assert str(error) == "Not Found"
        assert error.status_code == 404

    def test_creation_without_status(self):
        error = FetchError("Connection failed")
        
        assert error.status_code is None


class TestFetchUrl:
    def test_successful_html_fetch(self):
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com"
            mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
            mock_response.text = "<html><body>Hello World</body></html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            html, meta = fetch_url("https://example.com")
            
            assert "Hello World" in html
            assert meta.status_code == 200
            assert meta.is_pdf is False

    def test_pdf_response(self):
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com/document.pdf"
            mock_response.headers = {"Content-Type": "application/pdf"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            html, meta = fetch_url("https://example.com/document.pdf")
            
            assert meta.is_pdf is True
            assert html == ""

    def test_xhtml_content(self):
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com"
            mock_response.headers = {"Content-Type": "application/xhtml+xml"}
            mock_response.text = "<html><body>XHTML</body></html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            html, meta = fetch_url("https://example.com")
            
            assert "XHTML" in html

    def test_timeout_error(self):
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timed out")
            
            with pytest.raises(FetchError) as excinfo:
                fetch_url("https://example.com")
            
            assert "timed out" in str(excinfo.value)

    def test_request_exception(self):
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection refused")
            
            with pytest.raises(FetchError) as excinfo:
                fetch_url("https://example.com")
            
            assert "failed" in str(excinfo.value)

    def test_unsupported_content_type(self):
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com/data.json"
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            with pytest.raises(FetchError) as excinfo:
                fetch_url("https://example.com/data.json")
            
            assert "Unsupported content type" in str(excinfo.value)

    def test_custom_user_agent(self):
        with patch("jarvis_core.web_fetcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com"
            mock_response.headers = {"Content-Type": "text/html"}
            mock_response.text = "<html></html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            fetch_url("https://example.com", user_agent="CustomBot/1.0")
            
            call_args = mock_get.call_args
            assert "CustomBot/1.0" in call_args.kwargs["headers"]["User-Agent"]


class TestLoadUrlAsDocument:
    def test_with_prefetched_html(self):
        html = "<html><head><title>Test Page</title></head><body>Content</body></html>"
        meta = FetchMeta(
            final_url="https://example.com/page",
            status_code=200,
            content_type="text/html",
            is_pdf=False,
        )
        
        with patch("jarvis_core.web_fetcher.extract_main_text") as mock_extract, \
             patch("jarvis_core.web_fetcher.extract_title") as mock_title:
            mock_extract.return_value = "Content"
            mock_title.return_value = "Test Page"
            
            doc = load_url_as_document("https://example.com/page", html=html, meta=meta)
            
            assert doc.source == "url"
            assert "example.com" in doc.locator_base

    def test_pdf_url_raises_error(self):
        meta = FetchMeta(
            final_url="https://example.com/paper.pdf",
            status_code=200,
            content_type="application/pdf",
            is_pdf=True,
        )
        
        with pytest.raises(FetchError) as excinfo:
            load_url_as_document("https://example.com/paper.pdf", html="", meta=meta)
        
        assert "PDF" in str(excinfo.value)


class TestDefaultUserAgent:
    def test_contains_browser_info(self):
        assert "Mozilla" in DEFAULT_USER_AGENT
    
    def test_contains_jarvis(self):
        assert "Jarvis" in DEFAULT_USER_AGENT
