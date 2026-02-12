from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from jarvis_core.submission.package_builder import (
    build_submission_package,
    is_ready_to_submit,
    _build_diff_report,
    _build_zip,
    _find_previous_submission_dir,
    _resolve_previous_files,
    _run_single_check,
)


def test_is_ready_to_submit_uses_p6_checker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._resolve_run_dir",
        lambda _run_id: tmp_path,
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._check_p6_ready",
        lambda _run_dir: (True, "p6_ready.json:ready"),
    )

    ready, details = is_ready_to_submit("run-1")
    assert ready is True
    assert "p6_ready" in details


def test_build_submission_package_raises_if_run_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._resolve_run_dir", lambda _rid: None
    )
    with pytest.raises(FileNotFoundError):
        build_submission_package("missing-run", "1.0.0", "advisor")


def test_build_submission_package_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data_runs_dir = tmp_path / "data" / "runs"
    logs_runs_dir = tmp_path / "logs" / "runs"
    run_dir = logs_runs_dir / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)

    thesis_docx = run_dir / "thesis.docx"
    thesis_pdf = run_dir / "thesis.pdf"
    slides_pptx = run_dir / "slides.pptx"
    qa_pdf = run_dir / "qa_report.pdf"
    report_md = run_dir / "report.md"
    for p in [thesis_docx, thesis_pdf, slides_pptx, qa_pdf, report_md]:
        p.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr("jarvis_core.submission.package_builder.DATA_RUNS_DIR", data_runs_dir)
    monkeypatch.setattr("jarvis_core.submission.package_builder.LOGS_RUNS_DIR", logs_runs_dir)
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._resolve_run_dir",
        lambda _run_id: run_dir,
    )

    rules = {
        "defaults": {"project": "Demo", "author_name": "Alice"},
        "files": {
            "thesis_docx": "thesis_{version}.docx",
            "thesis_pdf": "thesis_{version}.pdf",
            "slides_pptx": "slides_{version}.pptx",
            "qa_report": "qa_{version}.pdf",
            "manifest": "manifest_{version}.json",
            "changelog": "changelog_{version}.md",
        },
    }
    checklist_config = {"checks": []}

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._load_yaml",
        lambda path: rules if path.name == "naming_rules.yaml" else checklist_config,
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._discover_artifacts",
        lambda _run_dir: {
            "thesis_docx": thesis_docx,
            "thesis_pdf": thesis_pdf,
            "slides_pptx": slides_pptx,
            "qa_report": qa_pdf,
            "manifest": None,
            "report_md": report_md,
        },
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._run_checklist",
        lambda *_args, **_kwargs: {
            "blocked": False,
            "checks": [{"id": "c1", "title": "ok", "status": "pass", "details": ""}],
            "qa": {"errors": 0, "warnings": 0, "major_warnings": []},
            "impact": {"has_impact": False, "details": ""},
        },
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._build_diff_report",
        lambda *args, **kwargs: {"diff": "ok"},
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder.generate_changelog",
        lambda **kwargs: SimpleNamespace(summary_lines=["summary line"]),
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder.generate_email_draft",
        lambda **kwargs: SimpleNamespace(
            subject="Submission Draft",
            body="Body",
            recipient_type=kwargs["recipient_type"],
        ),
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._build_zip",
        lambda submission_root, submission_version, run_id, blocked: submission_root
        / f"{run_id}-{submission_version}-{blocked}.zip",
    )

    result = build_submission_package("run-1", "1.0.0", "advisor")

    assert result.blocked is False
    assert result.changelog_path.name == "changelog_1.0.0.md"
    assert result.email_path.exists()
    assert result.check_report_path.exists()
    assert result.check_report_md_path.exists()
    assert result.package_path.name.endswith(".zip")


def test_run_single_check_covers_special_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    docx_path = tmp_path / "thesis.docx"
    docx_path.write_text("x", encoding="utf-8")
    pptx_path = tmp_path / "slides.pptx"
    pptx_path.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._check_p6_ready",
        lambda _run_dir: (False, "not ready"),
    )
    result = _run_single_check({"id": "p6", "type": "p6_ready"}, tmp_path, {}, [])
    assert result["status"] == "fail"
    assert result["details"] == "not ready"

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._extract_qa_summary",
        lambda _run_dir: {"errors": 2},
    )
    result = _run_single_check({"id": "qa", "type": "qa_error_zero"}, tmp_path, {}, [])
    assert result["status"] == "fail"
    assert result["details"] == "errors=2"

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._extract_metric_from_files",
        lambda *_args, **_kwargs: 3,
    )
    result = _run_single_check({"id": "fig", "type": "figure_reference_zero"}, tmp_path, {}, [])
    assert result["status"] == "fail"
    assert result["details"] == "broken=3"

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._extract_metric_from_files",
        lambda *_args, **_kwargs: None,
    )
    result = _run_single_check({"id": "fig", "type": "figure_reference_zero"}, tmp_path, {}, [])
    assert result["status"] == "fail"
    assert result["details"] == "report not found"

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._extract_metric_from_files",
        lambda *_args, **_kwargs: 5,
    )
    result = _run_single_check({"id": "unused", "type": "unused_references"}, tmp_path, {}, [])
    assert result["status"] == "warn"
    assert result["details"] == "unused=5"

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder.extract_docx_sections",
        lambda _docx: ([], 0),
    )
    result = _run_single_check(
        {"id": "docx", "type": "docx_headings"},
        tmp_path,
        {"thesis_docx": docx_path},
        [],
    )
    assert result["status"] == "fail"
    assert result["details"] == "no headings"

    result = _run_single_check({"id": "slide", "type": "slide_titles"}, tmp_path, {}, [])
    assert result["status"] == "fail"
    assert result["details"] == "slides not found"

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder.extract_pptx_slides",
        lambda _pptx: [(1, "Intro only")],
    )
    result = _run_single_check(
        {"id": "slide", "type": "slide_titles"},
        tmp_path,
        {"slides_pptx": pptx_path},
        [],
    )
    assert result["status"] == "fail"
    assert "conclusion=False" in result["details"]

    result = _run_single_check({"id": "mail", "type": "email_attachments"}, tmp_path, {}, [])
    assert result["status"] == "fail"
    assert result["details"] == "attachments empty"


def test_resolve_previous_files_with_zip(tmp_path: Path) -> None:
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    (old_dir / "legacy.docx").write_text("doc", encoding="utf-8")
    (old_dir / "slides.pptx").write_text("slides", encoding="utf-8")
    (old_dir / "report.md").write_text("report", encoding="utf-8")

    zip_path = tmp_path / "prev.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_path in old_dir.iterdir():
            zf.write(file_path, arcname=file_path.name)

    files, temp_dir = _resolve_previous_files("2.0.0", str(zip_path), "run-1")
    try:
        assert temp_dir is not None
        assert files["thesis_docx"] is not None
        assert files["slides_pptx"] is not None
        assert files["report_md"] is not None
    finally:
        if temp_dir:
            for child in temp_dir.rglob("*"):
                if child.is_file():
                    child.unlink()
            for child in sorted(temp_dir.rglob("*"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            if temp_dir.exists():
                temp_dir.rmdir()


def test_find_previous_submission_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data_runs_dir = tmp_path / "data" / "runs"
    base = data_runs_dir / "run-42" / "submission"
    (base / "1.0.0").mkdir(parents=True)
    (base / "1.1.0").mkdir(parents=True)
    (base / "2.0.0").mkdir(parents=True)
    monkeypatch.setattr("jarvis_core.submission.package_builder.DATA_RUNS_DIR", data_runs_dir)

    prev = _find_previous_submission_dir("2.0.0", "run-42")
    assert prev is not None
    assert prev.name == "1.1.0"


def test_build_diff_report_cleans_temp_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    temp_dir = tmp_path / "temp-prev"
    temp_dir.mkdir()
    called = {"cleaned": False}

    monkeypatch.setattr(
        "jarvis_core.submission.package_builder._resolve_previous_files",
        lambda *_args: (
            {
                "thesis_docx": None,
                "slides_pptx": None,
                "report_md": None,
            },
            temp_dir,
        ),
    )
    monkeypatch.setattr(
        "jarvis_core.submission.package_builder.generate_diff_report",
        lambda **kwargs: {"ok": True, "kwargs": kwargs},
    )

    def _fake_rmtree(path: Path, ignore_errors: bool = True) -> None:
        assert path == temp_dir
        assert ignore_errors is True
        called["cleaned"] = True

    monkeypatch.setattr("jarvis_core.submission.package_builder.shutil.rmtree", _fake_rmtree)

    result = _build_diff_report("1.0", {"thesis_docx": None, "slides_pptx": None}, None, "run")
    assert result["ok"] is True
    assert called["cleaned"] is True


def test_build_zip_creates_blocked_archive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data_runs_dir = tmp_path / "data" / "runs"
    run_id = "run-zip"
    submission_version = "1.0.0"
    submission_root = data_runs_dir / run_id / "submission" / submission_version
    submission_root.mkdir(parents=True)
    (submission_root / "03_reports").mkdir(parents=True, exist_ok=True)
    (submission_root / "03_reports" / "check_report.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("jarvis_core.submission.package_builder.DATA_RUNS_DIR", data_runs_dir)
    zip_path = _build_zip(submission_root, submission_version, run_id, blocked=True)

    assert zip_path.exists()
    assert "_BLOCKED" in zip_path.name
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert any(name.endswith("03_reports/check_report.json") for name in names)
