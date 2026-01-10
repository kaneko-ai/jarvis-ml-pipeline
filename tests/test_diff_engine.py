"""Tests for submission.diff_engine module."""

from pathlib import Path

from jarvis_core.submission.diff_engine import (
    SectionDiff,
    DiffReport,
    diff_sections,
    extract_md_sections,
    _summarize_text_change,
    _slide_sort_key,
    _slide_number_from_name,
)


class TestSectionDiff:
    def test_creation(self):
        diff = SectionDiff(section="Introduction", summary="更新（変更度 15%）")
        assert diff.section == "Introduction"
        assert "更新" in diff.summary


class TestDiffReport:
    def test_is_empty_true(self):
        report = DiffReport(docx_sections=[], md_sections=[], pptx_sections=[])
        assert report.is_empty() is True

    def test_is_empty_false_with_docx(self):
        report = DiffReport(
            docx_sections=[SectionDiff("Test", "Test")],
            md_sections=[],
            pptx_sections=[],
        )
        assert report.is_empty() is False

    def test_is_empty_false_with_md(self):
        report = DiffReport(
            docx_sections=[],
            md_sections=[SectionDiff("Test", "Test")],
            pptx_sections=[],
        )
        assert report.is_empty() is False


class TestDiffSections:
    def test_no_change(self):
        old = [("Section1", "Same content")]
        new = [("Section1", "Same content")]
        
        diffs = diff_sections(old, new)
        
        assert len(diffs) == 0

    def test_new_section_added(self):
        old = []
        new = [("NewSection", "New content")]
        
        diffs = diff_sections(old, new)
        
        assert len(diffs) == 1
        assert "追加" in diffs[0].summary

    def test_section_deleted(self):
        old = [("OldSection", "Old content")]
        new = []
        
        diffs = diff_sections(old, new)
        
        assert len(diffs) == 1
        assert "削除" in diffs[0].summary

    def test_section_modified(self):
        old = [("Section", "Original text here")]
        new = [("Section", "Completely different text now")]
        
        diffs = diff_sections(old, new)
        
        assert len(diffs) == 1
        assert "更新" in diffs[0].summary


class TestExtractMdSections:
    def test_extract_from_md_file(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Section 1\nContent 1\n\n# Section 2\nContent 2\n")
        
        sections = extract_md_sections(md_file)
        
        assert len(sections) == 2
        assert sections[0][0] == "Section 1"
        assert sections[1][0] == "Section 2"

    def test_extract_from_nonexistent_file(self, tmp_path):
        sections = extract_md_sections(tmp_path / "nonexistent.md")
        assert sections == []


class TestHelperFunctions:
    def test_summarize_text_change_short(self):
        result = _summarize_text_change("追加", "Short text")
        assert "追加" in result
        assert "Short text" in result

    def test_summarize_text_change_long(self):
        long_text = "A" * 200
        result = _summarize_text_change("追加", long_text)
        assert "..." in result
        assert len(result) < 150

    def test_slide_number_from_name(self):
        assert _slide_number_from_name("ppt/slides/slide1.xml") == 1
        assert _slide_number_from_name("ppt/slides/slide10.xml") == 10
        assert _slide_number_from_name("unknown") == 0

    def test_slide_sort_key(self):
        result = _slide_sort_key("ppt/slides/slide5.xml")
        assert result[0] == 5
