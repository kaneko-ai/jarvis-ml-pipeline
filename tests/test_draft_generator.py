"""Simplified tests for writing.draft_generator module."""

from jarvis_core.writing.draft_generator import (
    _now,
    _safe_read_json,
    generate_markdown_research_plan,
    generate_markdown_thesis_outline,
    generate_markdown_thesis_draft,
    _write_text,
)


class TestNow:
    def test_returns_iso_format(self):
        result = _now()
        assert "T" in result  # ISO format has T separator


class TestSafeReadJson:
    def test_valid_file(self, tmp_path):
        file = tmp_path / "test.json"
        file.write_text('{"key": "value"}')

        result = _safe_read_json(file)

        assert result["key"] == "value"

    def test_missing_file(self, tmp_path):
        result = _safe_read_json(tmp_path / "missing.json")

        assert result == {}


class TestGenerateMarkdownResearchPlan:
    def test_generates_markdown(self, tmp_path):
        claims = []  # Empty claims

        result = generate_markdown_research_plan(tmp_path, claims)

        assert isinstance(result, str)


class TestGenerateMarkdownThesisOutline:
    def test_generates_markdown(self, tmp_path):
        claims = []

        result = generate_markdown_thesis_outline(tmp_path, claims)

        assert isinstance(result, str)


class TestGenerateMarkdownThesisDraft:
    def test_generates_markdown(self, tmp_path):
        claims = []

        result = generate_markdown_thesis_draft(tmp_path, claims)

        assert isinstance(result, str)


class TestWriteText:
    def test_writes_file(self, tmp_path):
        path = tmp_path / "output.md"

        _write_text(path, "# Title\n\nContent")

        assert path.exists()
        assert "Title" in path.read_text()
