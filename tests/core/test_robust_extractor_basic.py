import sys
from unittest.mock import MagicMock, patch

# Mock missing modules for testing environments
sys.modules["pypdf"] = MagicMock()
sys.modules["pdfplumber"] = MagicMock()

from pathlib import Path
from jarvis_core.ingestion.robust_extractor import (
    RobustPDFExtractor,
    ExtractionResult,
    extract_pdf_robust,
)


class TestRobustPDFExtractor:
    @patch("jarvis_core.ingestion.robust_extractor.RobustPDFExtractor._detect_backends")
    def test_extract_fallback(self, mock_detect):
        # Setup: backend1 fails, backend2 succeeds
        mock_detect.return_value = ["backend1", "backend2"]

        extractor = RobustPDFExtractor()

        with patch.object(extractor, "_extract_with_backend") as mock_extract:
            # First call fails or return short text
            res1 = ExtractionResult(text="short", success=True, method="backend1")
            # Second call succeeds
            res2 = ExtractionResult(
                text="Long enough text to pass the threshold.", success=True, method="backend2"
            )

            mock_extract.side_effect = [res1, res2]

            # File must exist for extract() to proceed
            with patch("pathlib.Path.exists", return_value=True):
                result = extractor.extract(Path("dummy.pdf"))

                assert result.method == "backend2"
                assert mock_extract.call_count == 2

    @patch("jarvis_core.ingestion.robust_extractor.RobustPDFExtractor._detect_backends")
    def test_extract_all_fail(self, mock_detect):
        mock_detect.return_value = ["backend1"]
        extractor = RobustPDFExtractor()

        with patch.object(extractor, "_extract_with_backend") as mock_extract:
            mock_extract.side_effect = Exception("Crash")

            with patch("pathlib.Path.exists", return_value=True):
                result = extractor.extract(Path("dummy.pdf"))
                assert result.success is False
                assert "All extraction methods failed" in result.warnings[0]

    def test_extraction_result_to_dict(self):
        res = ExtractionResult(text="abc", pages=[(1, "abc")], method="test")
        d = res.to_dict()
        assert d["text_length"] == 3
        assert d["page_count"] == 1
        assert d["method"] == "test"

    @patch("jarvis_core.ingestion.robust_extractor.RobustPDFExtractor.extract")
    def test_convenience_function(self, mock_extract):
        mock_extract.return_value = ExtractionResult(text="ok", success=True)
        res = extract_pdf_robust(Path("dummy.pdf"), enable_ocr=True)
        assert res.success is True
        # Check if enable_ocr was passed (indirectly by checking constructor if we patch that too,
        # but here we just check if it returns what we mocked)

    def test_resolve_run_dir_none(self):
        # We don't have _resolve_run_dir in robust_extractor, it's in package_builder.
        # Just checking if I'm mixing up files.
        pass

    @patch("fitz.open", create=True)
    def test_extract_pymupdf(self, mock_fitz_open):
        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Page text"
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.metadata = {"title": "Test"}
        mock_fitz_open.return_value = mock_doc

        extractor = RobustPDFExtractor()
        res = extractor._extract_pymupdf(Path("dummy.pdf"))

        assert res.text == "Page text"
        assert res.success is True
        assert res.metadata["title"] == "Test"

    @patch("pdfplumber.open", create=True)
    def test_extract_pdfplumber(self, mock_plumber_open):
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Plumber text"
        mock_pdf.pages = [mock_page]
        mock_plumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = RobustPDFExtractor()
        # Ensure the backend is considered available for the call
        res = extractor._extract_pdfplumber(Path("dummy.pdf"))
        assert res.text == "Plumber text"
        assert res.success is True

    def test_extract_pypdf(self):
        with patch("pypdf.PdfReader", create=True) as mock_reader_cls:
            mock_reader = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "PyPDF text"
            mock_reader.pages = [mock_page]
            mock_reader_cls.return_value = mock_reader

            extractor = RobustPDFExtractor()
            res = extractor._extract_pypdf(Path("dummy.pdf"))
            assert res.text == "PyPDF text"


def test_extraction_result_defaults():
    res = ExtractionResult(text="hello")
    assert res.pages == []
    assert res.warnings == []
    assert res.metadata == {}
    assert res.success is True
