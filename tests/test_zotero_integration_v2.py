"""Tests for jarvis_core.zotero module.

Tests for bibtex_export.py to improve coverage.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSlugify:
    """Tests for _slugify function."""

    def test_slugify_basic(self):
        from jarvis_core.zotero.bibtex_export import _slugify

        result = _slugify("Hello World!")
        assert result == "Hello_World"

    def test_slugify_empty(self):
        from jarvis_core.zotero.bibtex_export import _slugify

        result = _slugify("")
        assert result == "untitled"

    def test_slugify_max_len(self):
        from jarvis_core.zotero.bibtex_export import _slugify

        result = _slugify("A" * 100, max_len=10)
        assert len(result) == 10


class TestJournalShort:
    """Tests for _journal_short function."""

    def test_journal_short_basic(self):
        from jarvis_core.zotero.bibtex_export import _journal_short

        result = _journal_short("Nature Medicine")
        assert len(result) <= 12

    def test_journal_short_empty(self):
        from jarvis_core.zotero.bibtex_export import _journal_short

        result = _journal_short("")
        assert result == "Journal"


class TestFirstAuthor:
    """Tests for _first_author function."""

    def test_first_author_list(self):
        from jarvis_core.zotero.bibtex_export import _first_author

        result = _first_author(["Smith, John", "Doe, Jane"])
        assert result == "Smith"

    def test_first_author_string(self):
        from jarvis_core.zotero.bibtex_export import _first_author

        result = _first_author("Smith, John; Doe, Jane")
        assert result == "Smith"

    def test_first_author_none(self):
        from jarvis_core.zotero.bibtex_export import _first_author

        result = _first_author(None)
        assert result == "Unknown"

    def test_first_author_no_comma(self):
        from jarvis_core.zotero.bibtex_export import _first_author

        result = _first_author(["John Smith"])
        assert result == "Smith"


class TestSafeKey:
    """Tests for safe_key function."""

    def test_safe_key_basic(self):
        from jarvis_core.zotero.bibtex_export import safe_key

        paper = {"authors": ["Smith, J"], "year": 2024, "journal": "Nature", "title": "Test"}
        existing = {}
        key = safe_key(paper, existing)
        assert "Smith" in key
        assert "2024" in key

    def test_safe_key_duplicate(self):
        from jarvis_core.zotero.bibtex_export import safe_key

        paper = {"authors": ["Smith, J"], "year": 2024, "journal": "Nature", "title": "Test"}
        existing = {}
        key1 = safe_key(paper, existing)
        key2 = safe_key(paper, existing)
        assert key1 != key2  # Second key should have suffix


class TestExportBibtex:
    """Tests for export_bibtex function."""

    def test_export_bibtex_no_run_dir(self):
        from jarvis_core.zotero.bibtex_export import export_bibtex

        with pytest.raises(FileNotFoundError):
            export_bibtex("nonexistent_run")

    def test_export_bibtex_empty_papers(self):
        from jarvis_core.zotero.bibtex_export import export_bibtex

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            run_dir = source_dir / "test_run"
            run_dir.mkdir()

            # Create empty papers.jsonl
            (run_dir / "papers.jsonl").write_text("", encoding="utf-8")

            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            result = export_bibtex("test_run", source_runs_dir=source_dir, output_base_dir=output_dir)
            assert result.endswith("refs.bib")

    def test_export_bibtex_with_papers(self):
        import json

        from jarvis_core.zotero.bibtex_export import export_bibtex

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            run_dir = source_dir / "test_run"
            run_dir.mkdir()

            # Create papers.jsonl with test data
            papers_data = [
                {"title": "Test Paper", "authors": ["Smith, J"], "year": 2024, "journal": "Nature"},
                {"title": "Another Paper", "authors": ["Doe, J"], "year": 2023, "doi": "10.1234/test"},
            ]
            with open(run_dir / "papers.jsonl", "w", encoding="utf-8") as f:
                for p in papers_data:
                    f.write(json.dumps(p) + "\n")

            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            result = export_bibtex("test_run", source_runs_dir=source_dir, output_base_dir=output_dir)
            
            # Verify output file exists and contains entries
            bib_path = Path(result)
            assert bib_path.exists()
            content = bib_path.read_text(encoding="utf-8")
            assert "@article{" in content
            assert "Test Paper" in content
