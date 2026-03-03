"""Tests for CLI command registration and help text."""
import pytest
from jarvis_cli import main


class TestCLICommands:
    EXPECTED_COMMANDS = [
        "run", "search", "merge", "note", "citation", "citation-stance",
        "prisma", "evidence", "score", "screen", "browse", "skills",
        "mcp", "orchestrate", "obsidian-export", "semantic-search",
        "contradict", "zotero-sync", "pdf-extract", "deep-research",
        "citation-graph", "pipeline",
    ]

    def test_command_count(self):
        assert len(self.EXPECTED_COMMANDS) == 22

    def test_help_returns_zero(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_no_command_returns_zero(self):
        result = main([])
        assert result == 0

    def test_each_command_has_help(self):
        for cmd in self.EXPECTED_COMMANDS:
            with pytest.raises(SystemExit) as exc_info:
                main([cmd, "--help"])
            assert exc_info.value.code == 0, f"Command '{cmd}' --help failed"

    def test_search_missing_query(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["search"])
        assert exc_info.value.code == 2

    def test_evidence_with_file(self, sample_papers_json):
        result = main(["evidence", sample_papers_json])
        assert result == 0 or result is None
