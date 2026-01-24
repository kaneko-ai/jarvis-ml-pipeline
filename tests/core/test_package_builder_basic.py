import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from jarvis_core.submission.package_builder import (
    _resolve_run_dir,
    _discover_artifacts,
    _apply_naming_rules,
    _ensure_structure,
    _write_submission_manifest,
    SubmissionResult,
)

@pytest.fixture
def temp_run_dir(tmp_path):
    run_dir = tmp_path / "run_123"
    run_dir.mkdir()
    (run_dir / "thesis.docx").write_text("docx content")
    (run_dir / "thesis.pdf").write_text("pdf content")
    (run_dir / "slides.pptx").write_text("pptx content")
    (run_dir / "qa_report.pdf").write_text("qa content")
    (run_dir / "report.md").write_text("md content")
    return run_dir

class TestPackageBuilderInternal:
    def test_resolve_run_dir(self, tmp_path):
        # We need to patch DATA_RUNS_DIR and LOGS_RUNS_DIR because they are constants at module level
        with patch("jarvis_core.submission.package_builder.DATA_RUNS_DIR", tmp_path / "data"):
            with patch("jarvis_core.submission.package_builder.LOGS_RUNS_DIR", tmp_path / "logs"):
                data_dir = tmp_path / "data" / "run1"
                data_dir.mkdir(parents=True)
                
                assert _resolve_run_dir("run1") == data_dir
                assert _resolve_run_dir("nonexistent") is None

    def test_discover_artifacts(self, temp_run_dir):
        artifacts = _discover_artifacts(temp_run_dir)
        assert artifacts["thesis_docx"] == temp_run_dir / "thesis.docx"
        assert artifacts["thesis_pdf"] == temp_run_dir / "thesis.pdf"
        assert artifacts["slides_pptx"] == temp_run_dir / "slides.pptx"
        assert artifacts["qa_report"] == temp_run_dir / "qa_report.pdf"
        assert artifacts["report_md"] == temp_run_dir / "report.md"

    def test_apply_naming_rules(self):
        rules = {
            "thesis_docx": "Paper_{project}_{version}.docx",
            "manifest": "manifest_{run_id}.json"
        }
        context = {"project": "P1", "version": "1.0", "run_id": "R1"}
        named = _apply_naming_rules(rules, context)
        assert named["thesis_docx"] == "Paper_P1_1.0.docx"
        assert named["manifest"] == "manifest_R1.json"

    def test_ensure_structure(self, tmp_path):
        root = tmp_path / "submit"
        structure = _ensure_structure(root)
        assert (root / "01_documents").exists()
        assert structure["documents"] == root / "01_documents"

    def test_write_submission_manifest(self, tmp_path):
        structure = {"manifest": tmp_path}
        artifacts = {"thesis_pdf": Path("source.pdf")}
        named_files = {"manifest": "m.json"}
        
        manifest_path = _write_submission_manifest("R1", "V1", artifacts, structure, named_files)
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["run_id"] == "R1"
        assert data["artifacts"]["thesis_pdf"] == "source.pdf"

    def test_run_checklist(self, temp_run_dir):
        from jarvis_core.submission.package_builder import _run_checklist
        config = {
            "checks": [
                {"id": "c1", "title": "Check 1", "type": "required_files", "required": ["thesis_pdf"], "severity": "fail"},
                {"id": "c2", "title": "Check 2", "type": "required_files", "required": ["nonexistent"], "severity": "warn"}
            ]
        }
        artifacts = {"thesis_pdf": Path("exists.pdf")}
        attachments = ["exists.pdf"]
        
        # We need to mock _extract_qa_summary and _extract_impact_summary as they search the dir
        with patch("jarvis_core.submission.package_builder._extract_qa_summary", return_value={"errors": 0, "warnings": 0, "major_warnings": []}):
            with patch("jarvis_core.submission.package_builder._extract_impact_summary", return_value={"has_impact": False, "details": ""}):
                res = _run_checklist(config, temp_run_dir, artifacts, attachments)
                assert res["blocked"] is False
                assert len(res["checks"]) == 2
                assert res["checks"][0]["status"] == "pass"
                assert res["checks"][1]["status"] == "fail" # because 'nonexistent' is missing in artifacts
                assert res["checks"][1]["severity"] == "warn"

    def test_run_checklist_blocking(self, temp_run_dir):
        from jarvis_core.submission.package_builder import _run_checklist
        config = {
            "checks": [
                {"id": "c1", "title": "Check 1", "type": "required_files", "required": ["thesis_docx"], "severity": "fail"},
            ]
        }
        # thesis_docx is missing in artifacts
        artifacts = {"thesis_pdf": Path("exists.pdf")}
        attachments = ["exists.pdf"]
        
        with patch("jarvis_core.submission.package_builder._extract_qa_summary", return_value={"errors": 0}):
            with patch("jarvis_core.submission.package_builder._extract_impact_summary", return_value={}):
                res = _run_checklist(config, temp_run_dir, artifacts, attachments)
                assert res["blocked"] is True
                assert res["checks"][0]["status"] == "fail"

def test_submission_result_dataclass():
    res = SubmissionResult(
        run_id="R1", submission_version="V1", blocked=False,
        package_path=Path("p.zip"), submission_root=Path("r"),
        changelog_path=Path("c"), email_path=Path("e"),
        check_report_path=Path("cr.json"), check_report_md_path=Path("cr.md"),
        email_subject="S", email_body="B"
    )
    assert res.run_id == "R1"
