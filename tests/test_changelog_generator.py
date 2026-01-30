"""Tests for submission.changelog_generator module."""

from unittest.mock import MagicMock
from jarvis_core.submission.changelog_generator import (
    ChangeLogResult,
    generate_changelog,
    _build_summary,
    _build_reason_groups,
)
from jarvis_core.submission.diff_engine import DiffReport


class TestChangeLogResult:
    def test_creation(self):
        result = ChangeLogResult(
            summary_lines=["Line 1", "Line 2"],
            markdown="# Changelog\n",
        )
        assert len(result.summary_lines) == 2
        assert "# Changelog" in result.markdown


class TestBuildSummary:
    def test_empty_diff(self):
        diff_report = MagicMock(spec=DiffReport)
        diff_report.docx_sections = []
        diff_report.md_sections = []
        diff_report.pptx_sections = []

        summary = _build_summary(diff_report, {})

        assert any("初回提出" in s or "差分なし" in s for s in summary)

    def test_with_changes(self):
        diff_report = MagicMock(spec=DiffReport)
        diff_report.docx_sections = [MagicMock()]
        diff_report.md_sections = []
        diff_report.pptx_sections = []

        summary = _build_summary(diff_report, {})

        assert any("変更箇所 1 件" in s for s in summary)

    def test_with_qa_errors(self):
        diff_report = MagicMock(spec=DiffReport)
        diff_report.docx_sections = []
        diff_report.md_sections = []
        diff_report.pptx_sections = []

        checklist = {"qa": {"errors": 3}}
        summary = _build_summary(diff_report, checklist)

        assert any("QA ERROR: 3" in s for s in summary)


class TestBuildReasonGroups:
    def test_no_checks(self):
        result = _build_reason_groups({})
        assert result == {}

    def test_all_passed(self):
        checklist = {"checks": [{"status": "pass", "title": "Test"}]}
        result = _build_reason_groups(checklist)
        assert result == {}

    def test_failed_checks_grouped(self):
        checklist = {
            "checks": [
                {"status": "fail", "title": "Check 1", "reason_category": "カテゴリA"},
                {"status": "fail", "title": "Check 2", "reason_category": "カテゴリA"},
                {"status": "fail", "title": "Check 3", "reason_category": "カテゴリB"},
            ]
        }
        result = _build_reason_groups(checklist)

        assert "カテゴリA" in result
        assert len(result["カテゴリA"]) == 2
        assert "カテゴリB" in result


class TestGenerateChangelog:
    def test_generate_basic(self, tmp_path):
        diff_report = MagicMock(spec=DiffReport)
        diff_report.is_empty.return_value = True
        diff_report.docx_sections = []
        diff_report.md_sections = []
        diff_report.pptx_sections = []

        checklist = {
            "impact": {"has_impact": False, "details": ""},
            "qa": {"errors": 0, "warnings": 0},
            "checks": [],
        }

        output_path = tmp_path / "changelog.md"
        result = generate_changelog(
            run_id="test_run",
            submission_version="1.0",
            diff_report=diff_report,
            checklist=checklist,
            attachments=["file1.docx"],
            output_path=output_path,
        )

        assert isinstance(result, ChangeLogResult)
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "ChangeLog" in content
        assert "test_run" in content