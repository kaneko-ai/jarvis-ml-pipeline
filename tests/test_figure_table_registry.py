"""Tests for style.figure_table_registry module."""

from jarvis_core.style.figure_table_registry import (
    FigureEntry,
    RegistryIssue,
    scan_text,
)


class TestFigureEntry:
    def test_creation(self):
        entry = FigureEntry(
            fig_id="FIG1",
            placeholder_exists=True,
            referenced_in_text=True,
        )
        assert entry.fig_id == "FIG1"
        assert entry.placeholder_exists is True
        assert entry.referenced_in_text is True


class TestRegistryIssue:
    def test_creation(self):
        issue = RegistryIssue(
            issue_type="missing_reference",
            message="本文内参照が見つかりません",
            fig_id="FIG1",
        )
        assert issue.issue_type == "missing_reference"
        assert issue.fig_id == "FIG1"


class TestScanText:
    def test_figure_placeholder_found(self):
        text = "[[FIGURE_PLACEHOLDER:FIG1]] shows the result. See Fig. 1."
        result = scan_text(text)

        assert len(result["figures"]) == 1
        assert result["figures"][0]["fig_id"] == "FIG1"
        assert result["figures"][0]["referenced_in_text"] is True

    def test_table_placeholder_found(self):
        text = "[[TABLE_PLACEHOLDER:TABLE1]] displays data. Table 1 shows values."
        result = scan_text(text)

        assert len(result["tables"]) == 1
        assert result["tables"][0]["fig_id"] == "TABLE1"
        assert result["tables"][0]["referenced_in_text"] is True

    def test_missing_reference_issue(self):
        text = "[[FIGURE_PLACEHOLDER:FIG1]] here."
        result = scan_text(text)

        assert len(result["figures"]) == 1
        assert result["figures"][0]["referenced_in_text"] is False
        assert any(i["issue_type"] == "missing_reference" for i in result["issues"])

    def test_duplicate_id_issue(self):
        text = "[[FIGURE_PLACEHOLDER:FIG1]] and [[FIGURE_PLACEHOLDER:FIG1]] again."
        result = scan_text(text)

        assert any(i["issue_type"] == "duplicate_id" for i in result["issues"])

    def test_non_sequential_numbers_issue(self):
        text = "[[FIGURE_PLACEHOLDER:FIG1]] and [[FIGURE_PLACEHOLDER:FIG3]]. Fig. 1 and Fig. 3."
        result = scan_text(text)

        assert any(i["issue_type"] == "non_sequential_number" for i in result["issues"])

    def test_no_placeholders(self):
        text = "Normal text without any placeholders."
        result = scan_text(text)

        assert len(result["figures"]) == 0
        assert len(result["tables"]) == 0
        assert len(result["issues"]) == 0

    def test_multiple_figures_sequential(self):
        text = """
        [[FIGURE_PLACEHOLDER:FIG1]] data.
        [[FIGURE_PLACEHOLDER:FIG2]] more data.
        Figure 1 and Fig. 2 show results.
        """
        result = scan_text(text)

        assert len(result["figures"]) == 2
        # Should not have non_sequential issue
        non_seq_issues = [i for i in result["issues"] if i["issue_type"] == "non_sequential_number"]
        assert len(non_seq_issues) == 0
