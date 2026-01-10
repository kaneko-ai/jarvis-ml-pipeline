"""Comprehensive tests for submission.package_builder module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from jarvis_core.submission.package_builder import (
    SubmissionResult,
    is_ready_to_submit,
    _resolve_run_dir,
    _load_yaml,
    _ensure_structure,
    _discover_artifacts,
    _apply_naming_rules,
    _copy_artifacts,
    _build_attachment_list,
    _run_single_check,
    _infer_reason_category,
    _check_p6_ready,
    _extract_qa_summary,
    _extract_impact_summary,
    _extract_metric_from_files,
    _safe_load_json,
    _closest_previous_version,
    _version_key,
    _write_email_draft,
    _write_check_report,
)


class TestSubmissionResult:
    def test_creation(self):
        result = SubmissionResult(
            run_id="run-1",
            submission_version="v1.0",
            blocked=False,
            package_path=Path("pkg.zip"),
            submission_root=Path("submission"),
            changelog_path=Path("changelog.md"),
            email_path=Path("email.txt"),
            check_report_path=Path("report.json"),
            check_report_md_path=Path("report.md"),
            email_subject="Subject",
            email_body="Body",
        )
        
        assert result.run_id == "run-1"
        assert result.blocked is False


class TestResolveRunDir:
    def test_not_found(self):
        result = _resolve_run_dir("nonexistent-run-id-12345")
        assert result is None


class TestLoadYaml:
    def test_load_yaml(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2")
        
        result = _load_yaml(yaml_file)
        
        assert result["key"] == "value"
        assert len(result["list"]) == 2


class TestEnsureStructure:
    def test_creates_directories(self, tmp_path):
        submission_root = tmp_path / "submission"
        
        structure = _ensure_structure(submission_root)
        
        assert structure["documents"].exists()
        assert structure["slides"].exists()
        assert structure["reports"].exists()
        assert structure["manifest"].exists()
        assert structure["notes"].exists()
        assert structure["email"].exists()


class TestDiscoverArtifacts:
    def test_empty_directory(self, tmp_path):
        result = _discover_artifacts(tmp_path)
        
        assert all(v is None for v in result.values())

    def test_finds_docx(self, tmp_path):
        (tmp_path / "thesis.docx").write_text("mock docx")
        
        result = _discover_artifacts(tmp_path)
        
        assert result["thesis_docx"] is not None

    def test_finds_pptx(self, tmp_path):
        (tmp_path / "slides.pptx").write_text("mock pptx")
        
        result = _discover_artifacts(tmp_path)
        
        assert result["slides_pptx"] is not None

    def test_finds_pdf(self, tmp_path):
        (tmp_path / "thesis.pdf").write_text("mock pdf")
        
        result = _discover_artifacts(tmp_path)
        
        assert result["thesis_pdf"] is not None

    def test_finds_qa_pdf(self, tmp_path):
        (tmp_path / "qa_report.pdf").write_text("mock qa pdf")
        
        result = _discover_artifacts(tmp_path)
        
        assert result["qa_report"] is not None

    def test_finds_manifest(self, tmp_path):
        (tmp_path / "manifest.json").write_text('{"key": "value"}')
        
        result = _discover_artifacts(tmp_path)
        
        assert result["manifest"] is not None


class TestApplyNamingRules:
    def test_applies_context(self):
        files = {
            "thesis_docx": "thesis_{version}.docx",
            "slides_pptx": "slides_{version}_{project}.pptx",
        }
        context = {"version": "v1.0", "project": "JARVIS"}
        
        result = _apply_naming_rules(files, context)
        
        assert result["thesis_docx"] == "thesis_v1.0.docx"
        assert result["slides_pptx"] == "slides_v1.0_JARVIS.pptx"


class TestCopyArtifacts:
    def test_copies_files(self, tmp_path):
        # Create structure
        structure = _ensure_structure(tmp_path / "submission")
        
        # Create source file
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "thesis.docx"
        source_file.write_text("thesis content")
        
        artifacts = {"thesis_docx": source_file}
        named_files = {"thesis_docx": "thesis_v1.docx"}
        
        result = _copy_artifacts(artifacts, structure, named_files)
        
        assert result["thesis_docx"] is not None
        assert result["thesis_docx"].exists()


class TestBuildAttachmentList:
    def test_builds_list(self, tmp_path):
        structure = _ensure_structure(tmp_path)
        named_files = {
            "thesis_docx": "thesis.docx",
            "slides_pptx": "slides.pptx",
            "changelog": "changelog.md",
        }
        copied = {"thesis_docx": tmp_path / "thesis.docx"}
        manifest_path = tmp_path / "manifest.json"
        
        result = _build_attachment_list(structure, named_files, copied, manifest_path)
        
        assert "thesis.docx" in result
        assert "changelog.md" in result


class TestRunSingleCheck:
    def test_required_files_pass(self, tmp_path):
        item = {"id": "req1", "type": "required_files", "required": []}
        
        result = _run_single_check(item, tmp_path, {}, [])
        
        assert result["status"] == "pass"

    def test_required_files_fail(self, tmp_path):
        item = {"id": "req1", "type": "required_files", "required": ["thesis_docx"]}
        
        result = _run_single_check(item, tmp_path, {"thesis_docx": None}, [])
        
        assert result["status"] == "fail"

    def test_unknown_check_type(self, tmp_path):
        item = {"id": "unknown", "type": "unknown_type"}
        
        result = _run_single_check(item, tmp_path, {}, [])
        
        assert result["status"] == "warn"


class TestInferReasonCategory:
    def test_qa_category(self):
        assert _infer_reason_category("qa_check") == "根拠"

    def test_reference_category(self):
        assert _infer_reason_category("figure_reference") == "図表"

    def test_docx_category(self):
        assert _infer_reason_category("docx_headings") == "表現"

    def test_slide_category(self):
        assert _infer_reason_category("slide_titles") == "結論"

    def test_default_category(self):
        assert _infer_reason_category("other") == "その他"

    def test_none_input(self):
        assert _infer_reason_category(None) == "その他"


class TestCheckP6Ready:
    def test_not_found(self, tmp_path):
        ready, details = _check_p6_ready(tmp_path)
        
        assert ready is False
        assert "not found" in details

    def test_ready_true(self, tmp_path):
        (tmp_path / "p6_ready.json").write_text('{"READY_TO_SUBMIT": true}')
        
        ready, details = _check_p6_ready(tmp_path)
        
        assert ready is True

    def test_ready_false(self, tmp_path):
        (tmp_path / "ready.json").write_text('{"ready": false}')
        
        ready, details = _check_p6_ready(tmp_path)
        
        assert ready is False


class TestExtractQaSummary:
    def test_no_file(self, tmp_path):
        result = _extract_qa_summary(tmp_path)
        
        assert result["errors"] == 0
        assert result["warnings"] == 0

    def test_with_errors(self, tmp_path):
        (tmp_path / "qa_summary.json").write_text('{"error_count": 3, "warn_count": 5}')
        
        result = _extract_qa_summary(tmp_path)
        
        assert result["errors"] == 3
        assert result["warnings"] == 5


class TestExtractImpactSummary:
    def test_no_file(self, tmp_path):
        result = _extract_impact_summary(tmp_path)
        
        assert result["has_impact"] is False

    def test_with_impact(self, tmp_path):
        (tmp_path / "impact_summary.json").write_text('{"has_impact": true, "details": "High"}')
        
        result = _extract_impact_summary(tmp_path)
        
        assert result["has_impact"] is True


class TestExtractMetricFromFiles:
    def test_file_not_found(self, tmp_path):
        result = _extract_metric_from_files(tmp_path, ["missing.json"], "count")
        
        assert result is None

    def test_extracts_value(self, tmp_path):
        (tmp_path / "report.json").write_text('{"count": 42}')
        
        result = _extract_metric_from_files(tmp_path, ["report.json"], "count")
        
        assert result == 42


class TestSafeLoadJson:
    def test_valid_json(self, tmp_path):
        file = tmp_path / "test.json"
        file.write_text('{"key": "value"}')
        
        result = _safe_load_json(file)
        
        assert result["key"] == "value"

    def test_invalid_json(self, tmp_path):
        file = tmp_path / "test.json"
        file.write_text("not valid json")
        
        result = _safe_load_json(file)
        
        assert result == {}


class TestVersionKey:
    def test_simple_version(self):
        assert _version_key("1.0.0") == (1, 0, 0)

    def test_version_with_prefix(self):
        # 'v' is not a digit, so it becomes 0
        result = _version_key("v1.2.3")
        assert result[0] == 0  # 'v' -> 0
        assert len(result) >= 3  # Has multiple parts

    def test_version_with_dash(self):
        assert _version_key("1-2-3") == (1, 2, 3)


class TestClosestPreviousVersion:
    def test_finds_previous(self):
        result = _closest_previous_version("1.2", ["1.0", "1.1", "1.3"])
        
        assert result == "1.1"

    def test_no_previous(self):
        result = _closest_previous_version("1.0", ["1.1", "1.2"])
        
        assert result is None


class TestWriteEmailDraft:
    def test_writes_file(self, tmp_path):
        mock_draft = MagicMock()
        mock_draft.recipient_type = "advisor"
        mock_draft.subject = "Test Subject"
        mock_draft.body = "Test Body"
        
        result = _write_email_draft(tmp_path / "email", mock_draft)
        
        assert result.exists()
        content = result.read_text()
        assert "Test Subject" in content
        assert "Test Body" in content


class TestWriteCheckReport:
    def test_writes_both_formats(self, tmp_path):
        report = {
            "blocked": False,
            "checks": [{"title": "Test", "status": "pass", "details": "OK"}],
        }
        json_path = tmp_path / "report.json"
        md_path = tmp_path / "report.md"
        
        _write_check_report([json_path], [md_path], report)
        
        assert json_path.exists()
        assert md_path.exists()


class TestIsReadyToSubmit:
    def test_run_not_found(self):
        ready, reason = is_ready_to_submit("nonexistent-run-12345")
        
        assert ready is False
        assert "not found" in reason
