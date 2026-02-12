"""Coverage tests for jarvis_core.index_builder."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


def _setup_jarvis_tools_mock():
    """Set up mock for jarvis_tools.papers module."""
    papers_mod = ModuleType("jarvis_tools.papers")
    papers_mod.pubmed_esearch = MagicMock(return_value=["123"])
    papers_mod.pubmed_esummary = MagicMock(return_value=[])
    papers_mod.extract_text_from_pdf = MagicMock(return_value=["page1"])
    papers_mod.split_pages_into_chunks = MagicMock(return_value=[])
    papers_mod.PaperRecord = MagicMock()
    return papers_mod


class TestBuildIndex:
    def test_pubmed_no_query(self, tmp_path: Path) -> None:
        """source=pubmed but no query => no papers fetched."""
        papers_mod = _setup_jarvis_tools_mock()
        with patch.dict(
            sys.modules,
            {"jarvis_tools": ModuleType("jarvis_tools"), "jarvis_tools.papers": papers_mod},
        ):
            with patch("jarvis_core.index_builder.init_logger") as mock_logger:
                mock_logger.return_value = MagicMock()
                with patch("jarvis_core.index_builder.IndexRegistry") as MockReg:
                    MockReg.return_value = MagicMock()
                    from jarvis_core.index_builder import build_index

                    result = build_index(
                        query=None,
                        source="pubmed",
                        output_dir=str(tmp_path / "idx"),
                    )
        assert result["success"] is True
        assert result["paper_count"] == 0

    def test_pubmed_with_query(self, tmp_path: Path) -> None:
        """source=pubmed with query => fetch papers."""
        mock_paper = MagicMock()
        mock_paper.paper_id = "pmid123"
        mock_paper.pdf_path = None
        mock_paper.to_dict.return_value = {"pmid": "123", "title": "Test"}
        mock_paper.pmid = "123"

        papers_mod = _setup_jarvis_tools_mock()
        papers_mod.pubmed_esearch.return_value = ["123"]
        papers_mod.pubmed_esummary.return_value = [mock_paper]

        with patch.dict(
            sys.modules,
            {"jarvis_tools": ModuleType("jarvis_tools"), "jarvis_tools.papers": papers_mod},
        ):
            with patch("jarvis_core.index_builder.init_logger") as mock_logger:
                mock_logger.return_value = MagicMock()
                with patch("jarvis_core.index_builder.IndexRegistry") as MockReg:
                    MockReg.return_value = MagicMock()
                    from jarvis_core.index_builder import build_index

                    result = build_index(
                        query="cancer",
                        source="pubmed",
                        output_dir=str(tmp_path / "idx"),
                        max_papers=10,
                    )
        assert result["success"] is True
        assert result["paper_count"] == 1

    def test_local_pdf(self, tmp_path: Path) -> None:
        """source=local with local_pdf_dir."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "test.pdf").write_text("fake pdf content")

        mock_paper = MagicMock()
        mock_paper.paper_id = "test"
        mock_paper.pdf_path = str(pdf_dir / "test.pdf")
        mock_paper.to_dict.return_value = {"title": "test"}
        mock_paper.pmid = None

        mock_chunk = MagicMock()
        mock_chunk.to_dict.return_value = {"text": "chunk"}

        papers_mod = _setup_jarvis_tools_mock()
        papers_mod.PaperRecord.return_value = mock_paper
        papers_mod.extract_text_from_pdf.return_value = ["page1"]
        papers_mod.split_pages_into_chunks.return_value = [mock_chunk]

        with patch.dict(
            sys.modules,
            {"jarvis_tools": ModuleType("jarvis_tools"), "jarvis_tools.papers": papers_mod},
        ):
            with patch("jarvis_core.index_builder.init_logger") as mock_logger:
                mock_logger.return_value = MagicMock()
                with patch("jarvis_core.index_builder.IndexRegistry") as MockReg:
                    MockReg.return_value = MagicMock()
                    from jarvis_core.index_builder import build_index

                    result = build_index(
                        source="local",
                        local_pdf_dir=str(pdf_dir),
                        output_dir=str(tmp_path / "idx"),
                    )
        assert result["success"] is True

    def test_local_pdf_nonexistent_dir(self, tmp_path: Path) -> None:
        """source=local with nonexistent dir."""
        papers_mod = _setup_jarvis_tools_mock()
        with patch.dict(
            sys.modules,
            {"jarvis_tools": ModuleType("jarvis_tools"), "jarvis_tools.papers": papers_mod},
        ):
            with patch("jarvis_core.index_builder.init_logger") as mock_logger:
                mock_logger.return_value = MagicMock()
                with patch("jarvis_core.index_builder.IndexRegistry") as MockReg:
                    MockReg.return_value = MagicMock()
                    from jarvis_core.index_builder import build_index

                    result = build_index(
                        source="local",
                        local_pdf_dir=str(tmp_path / "nonexistent"),
                        output_dir=str(tmp_path / "idx"),
                    )
        assert result["success"] is True
        assert result["paper_count"] == 0

    def test_catastrophic_failure(self, tmp_path: Path) -> None:
        """Top-level exception => success=False."""
        papers_mod = _setup_jarvis_tools_mock()
        papers_mod.pubmed_esearch.side_effect = RuntimeError("network")
        with patch.dict(
            sys.modules,
            {"jarvis_tools": ModuleType("jarvis_tools"), "jarvis_tools.papers": papers_mod},
        ):
            with patch("jarvis_core.index_builder.init_logger") as mock_logger:
                mock_logger.return_value = MagicMock()
                from jarvis_core.index_builder import build_index

                result = build_index(
                    query="test",
                    source="pubmed",
                    output_dir=str(tmp_path / "idx"),
                )
        assert result["success"] is False
        assert "error" in result
