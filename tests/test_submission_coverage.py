"""Tests for submission module - Coverage improvement (FIXED)."""

import tempfile
from pathlib import Path


class TestSectionDiff:
    """Tests for SectionDiff dataclass."""

    def test_section_diff_creation(self):
        """Test SectionDiff creation."""
        from jarvis_core.submission.diff_engine import SectionDiff

        diff = SectionDiff(section="Introduction", summary="追加: New content")

        assert diff.section == "Introduction"
        assert diff.summary == "追加: New content"


class TestDiffReport:
    """Tests for DiffReport dataclass."""

    def test_diff_report_creation(self):
        """Test DiffReport creation."""
        from jarvis_core.submission.diff_engine import DiffReport

        report = DiffReport(
            docx_sections=[],
            md_sections=[],
            pptx_sections=[],
        )

        assert report.docx_sections == []
        assert report.is_empty()

    def test_is_empty_false(self):
        """Test is_empty when not empty."""
        from jarvis_core.submission.diff_engine import DiffReport, SectionDiff

        report = DiffReport(
            docx_sections=[SectionDiff(section="Intro", summary="Added")],
            md_sections=[],
            pptx_sections=[],
        )

        assert not report.is_empty()


class TestDiffFunctions:
    """Tests for diff functions."""

    def test_extract_md_sections_nonexistent(self):
        """Test extract_md_sections with nonexistent file."""
        from jarvis_core.submission.diff_engine import extract_md_sections

        result = extract_md_sections(Path("/nonexistent/file.md"))
        assert result == []

    def test_extract_md_sections(self):
        """Test extract_md_sections with real file."""
        from jarvis_core.submission.diff_engine import extract_md_sections

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Heading 1\nContent 1\n# Heading 2\nContent 2")
            f.flush()

            result = extract_md_sections(Path(f.name))

            assert len(result) == 2
            assert result[0][0] == "Heading 1"

    def test_extract_docx_sections_nonexistent(self):
        """Test extract_docx_sections with nonexistent file."""
        from jarvis_core.submission.diff_engine import extract_docx_sections

        # Returns list of sections, may return default section
        result, count = extract_docx_sections(Path("/nonexistent/file.docx"))
        # Just verify it doesn't crash
        assert isinstance(result, list)

    def test_extract_pptx_slides_nonexistent(self):
        """Test extract_pptx_slides with nonexistent file."""
        from jarvis_core.submission.diff_engine import extract_pptx_slides

        result = extract_pptx_slides(Path("/nonexistent/file.pptx"))
        assert result == []

    def test_diff_sections(self):
        """Test diff_sections function."""
        from jarvis_core.submission.diff_engine import diff_sections

        old = [("Intro", "Old content")]
        new = [("Intro", "New content"), ("Methods", "Methods content")]

        diffs = diff_sections(old, new)

        # Should detect changes
        assert len(diffs) >= 1

    def test_generate_diff_report(self):
        """Test generate_diff_report function."""
        from jarvis_core.submission.diff_engine import generate_diff_report

        report = generate_diff_report(
            current_docx=None,
            previous_docx=None,
            current_md=None,
            previous_md=None,
            current_pptx=None,
            previous_pptx=None,
        )

        assert report is not None
        assert report.is_empty()


class TestModuleImports:
    """Test module imports."""

    def test_submission_imports(self):
        """Test submission module imports."""
        from jarvis_core.submission import (
            diff_engine,
        )

        assert diff_engine is not None
