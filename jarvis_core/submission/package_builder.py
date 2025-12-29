from __future__ import annotations

import json
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .changelog_generator import generate_changelog
from .diff_engine import generate_diff_report, extract_docx_sections, extract_pptx_slides
from .email_generator import generate_email_draft


DATA_RUNS_DIR = Path("data/runs")
LOGS_RUNS_DIR = Path("logs/runs")
SUBMISSION_DIRNAME = "submission"


@dataclass
class SubmissionResult:
    run_id: str
    submission_version: str
    blocked: bool
    package_path: Path
    submission_root: Path
    changelog_path: Path
    email_path: Path
    check_report_path: Path
    check_report_md_path: Path
    email_subject: str
    email_body: str


def is_ready_to_submit(run_id: str) -> Tuple[bool, str]:
    run_dir = _resolve_run_dir(run_id)
    if run_dir is None:
        return False, "run not found"
    return _check_p6_ready(run_dir)


def build_submission_package(
    run_id: str,
    submission_version: str,
    recipient_type: str,
    previous_package_path: Optional[str] = None,
) -> SubmissionResult:
    run_dir = _resolve_run_dir(run_id)
    if run_dir is None:
        raise FileNotFoundError(f"Run {run_id} not found in data/runs or logs/runs")

    rules = _load_yaml(Path(__file__).with_name("naming_rules.yaml"))
    checklist_config = _load_yaml(Path(__file__).with_name("checklist.yaml"))
    templates_path = Path(__file__).with_name("email_templates.yaml")

    submission_root = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME / submission_version
    submission_root.mkdir(parents=True, exist_ok=True)

    structure = _ensure_structure(submission_root)
    artifacts = _discover_artifacts(run_dir)

    naming_context = {
        **(rules.get("defaults") or {}),
        "version": submission_version,
        "run_id": run_id,
    }
    named_files = _apply_naming_rules(rules.get("files") or {}, naming_context)

    copied = _copy_artifacts(artifacts, structure, named_files)
    manifest_path = _write_submission_manifest(run_id, submission_version, artifacts, structure, named_files)

    attachments = _build_attachment_list(structure, named_files, copied, manifest_path)
    check_report = _run_checklist(
        checklist_config,
        run_dir=run_dir,
        artifacts=artifacts,
        attachments=attachments,
    )

    diff_report = _build_diff_report(
        submission_version,
        artifacts,
        previous_package_path,
        run_id,
    )

    changelog_path = structure["reports"] / named_files["changelog"]
    changelog_result = generate_changelog(
        run_id=run_id,
        submission_version=submission_version,
        diff_report=diff_report,
        checklist=check_report,
        attachments=attachments,
        output_path=changelog_path,
    )

    email_context = {
        "project": naming_context.get("project", ""),
        "author_name": naming_context.get("author_name", ""),
        "submission_version": submission_version,
        "changelog_summary": "\n".join([f"- {line}" for line in changelog_result.summary_lines]),
    }
    email_draft = generate_email_draft(
        templates_path=templates_path,
        recipient_type=recipient_type,
        context=email_context,
        attachments=attachments,
    )

    email_path = _write_email_draft(structure["email"], email_draft)

    check_report_path = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME / "check_report.json"
    check_report_md_path = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME / "check_report.md"
    submission_check_report_path = structure["reports"] / "check_report.json"
    submission_check_report_md_path = structure["reports"] / "check_report.md"
    _write_check_report(
        [check_report_path, submission_check_report_path],
        [check_report_md_path, submission_check_report_md_path],
        check_report,
    )

    blocked = bool(check_report.get("blocked"))
    package_path = _build_zip(submission_root, submission_version, run_id, blocked)

    return SubmissionResult(
        run_id=run_id,
        submission_version=submission_version,
        blocked=blocked,
        package_path=package_path,
        submission_root=submission_root,
        changelog_path=changelog_path,
        email_path=email_path,
        check_report_path=check_report_path,
        check_report_md_path=check_report_md_path,
        email_subject=email_draft.subject,
        email_body=email_draft.body,
    )


def _resolve_run_dir(run_id: str) -> Optional[Path]:
    candidate = DATA_RUNS_DIR / run_id
    if candidate.exists():
        return candidate
    candidate = LOGS_RUNS_DIR / run_id
    if candidate.exists():
        return candidate
    return None


def _load_yaml(path: Path) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _ensure_structure(submission_root: Path) -> Dict[str, Path]:
    structure = {
        "documents": submission_root / "01_documents",
        "slides": submission_root / "02_slides",
        "reports": submission_root / "03_reports",
        "manifest": submission_root / "04_manifest",
        "notes": submission_root / "05_notes",
        "email": submission_root / "email_drafts",
    }
    for path in structure.values():
        path.mkdir(parents=True, exist_ok=True)
    return structure


def _discover_artifacts(run_dir: Path) -> Dict[str, Optional[Path]]:
    artifacts: Dict[str, Optional[Path]] = {
        "thesis_docx": None,
        "thesis_pdf": None,
        "slides_pptx": None,
        "qa_report": None,
        "manifest": None,
        "report_md": None,
    }

    if not run_dir.exists():
        return artifacts

    candidates = list(run_dir.glob("**/*"))
    for path in candidates:
        if not path.is_file():
            continue
        name_lower = path.name.lower()
        if path.suffix.lower() == ".docx" and artifacts["thesis_docx"] is None:
            artifacts["thesis_docx"] = path
        elif path.suffix.lower() == ".pptx" and artifacts["slides_pptx"] is None:
            artifacts["slides_pptx"] = path
        elif path.suffix.lower() == ".pdf":
            if "qa" in name_lower and artifacts["qa_report"] is None:
                artifacts["qa_report"] = path
            elif artifacts["thesis_pdf"] is None:
                artifacts["thesis_pdf"] = path
        elif path.suffix.lower() == ".json" and "manifest" in name_lower and artifacts["manifest"] is None:
            artifacts["manifest"] = path
        elif path.suffix.lower() == ".md" and path.name == "report.md" and artifacts["report_md"] is None:
            artifacts["report_md"] = path

    return artifacts


def _apply_naming_rules(files: Dict[str, str], context: Dict[str, str]) -> Dict[str, str]:
    named = {}
    for key, template in files.items():
        named[key] = template.format(**context)
    return named


def _copy_artifacts(
    artifacts: Dict[str, Optional[Path]],
    structure: Dict[str, Path],
    named_files: Dict[str, str],
) -> Dict[str, Optional[Path]]:
    copied: Dict[str, Optional[Path]] = {}
    mapping = {
        "thesis_docx": ("documents", named_files.get("thesis_docx")),
        "thesis_pdf": ("documents", named_files.get("thesis_pdf")),
        "slides_pptx": ("slides", named_files.get("slides_pptx")),
        "qa_report": ("reports", named_files.get("qa_report")),
        "manifest": ("manifest", named_files.get("manifest")),
    }
    for key, (folder, target_name) in mapping.items():
        source = artifacts.get(key)
        if source and target_name:
            destination = structure[folder] / target_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied[key] = destination
        else:
            copied[key] = None
    return copied


def _write_submission_manifest(
    run_id: str,
    submission_version: str,
    artifacts: Dict[str, Optional[Path]],
    structure: Dict[str, Path],
    named_files: Dict[str, str],
) -> Path:
    manifest_path = structure["manifest"] / named_files["manifest"]
    payload = {
        "run_id": run_id,
        "submission_version": submission_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {key: str(path) if path else None for key, path in artifacts.items()},
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def _build_attachment_list(
    structure: Dict[str, Path],
    named_files: Dict[str, str],
    copied: Dict[str, Optional[Path]],
    manifest_path: Path,
) -> List[str]:
    attachments = []
    for key in ["thesis_docx", "thesis_pdf", "slides_pptx", "qa_report"]:
        target = named_files.get(key)
        if target:
            attachments.append(target)
    if manifest_path:
        attachments.append(manifest_path.name)
    changelog_name = named_files.get("changelog")
    if changelog_name:
        attachments.append(changelog_name)
    return attachments


def _run_checklist(
    checklist_config: Dict[str, object],
    run_dir: Path,
    artifacts: Dict[str, Optional[Path]],
    attachments: List[str],
) -> Dict[str, object]:
    checks = []
    blocked = False

    for item in checklist_config.get("checks", []):
        result = _run_single_check(item, run_dir, artifacts, attachments)
        checks.append(result)
        if result["status"] == "fail" and item.get("severity") == "fail":
            blocked = True

    qa_summary = _extract_qa_summary(run_dir)
    impact = _extract_impact_summary(run_dir)

    return {
        "blocked": blocked,
        "checks": checks,
        "qa": qa_summary,
        "impact": impact,
    }


def _run_single_check(
    item: Dict[str, object],
    run_dir: Path,
    artifacts: Dict[str, Optional[Path]],
    attachments: List[str],
) -> Dict[str, object]:
    check_type = item.get("type")
    status = "pass"
    details = ""

    if check_type == "required_files":
        missing = [key for key in item.get("required", []) if not artifacts.get(key)]
        if missing:
            status = "fail"
            details = f"missing: {', '.join(missing)}"
    elif check_type == "p6_ready":
        ready, details = _check_p6_ready(run_dir)
        if not ready:
            status = "fail"
    elif check_type == "qa_error_zero":
        errors = _extract_qa_summary(run_dir).get("errors")
        if errors not in (0, "0"):
            status = "fail"
            details = f"errors={errors}"
    elif check_type == "figure_reference_zero":
        broken = _extract_metric_from_files(run_dir, ["figure_reference_report.json", "figure_refs.json"], "broken_count")
        if broken not in (0, "0", None):
            status = "fail"
            details = f"broken={broken}"
        elif broken is None:
            status = "fail"
            details = "report not found"
    elif check_type == "unused_references":
        unused = _extract_metric_from_files(run_dir, ["unused_references.json", "unused_refs.json"], "count")
        if unused not in (0, "0", None):
            status = "warn"
            details = f"unused={unused}"
    elif check_type == "docx_headings":
        docx = artifacts.get("thesis_docx")
        heading_count = 0
        if docx and docx.exists():
            _, heading_count = extract_docx_sections(docx)
        if heading_count == 0:
            status = "fail"
            details = "no headings"
    elif check_type == "slide_titles":
        pptx = artifacts.get("slides_pptx")
        if pptx and pptx.exists():
            slides = extract_pptx_slides(pptx)
            title_ok = bool(slides and slides[0][1].strip())
            conclusion_ok = any("結論" in text or "Conclusion" in text for _, text in slides)
            if not (title_ok and conclusion_ok):
                status = "fail"
                details = f"title={title_ok}, conclusion={conclusion_ok}"
        else:
            status = "fail"
            details = "slides not found"
    elif check_type == "email_attachments":
        if not attachments:
            status = "fail"
            details = "attachments empty"
    else:
        status = "warn"
        details = "unknown check type"

    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "status": status,
        "details": details,
        "severity": item.get("severity"),
        "reason_category": _infer_reason_category(item.get("id")),
    }


def _infer_reason_category(check_id: Optional[str]) -> str:
    if not check_id:
        return "その他"
    if "qa" in check_id:
        return "根拠"
    if "reference" in check_id:
        return "図表"
    if "docx" in check_id:
        return "表現"
    if "slide" in check_id:
        return "結論"
    return "その他"


def _check_p6_ready(run_dir: Path) -> Tuple[bool, str]:
    candidates = [
        run_dir / "p6_ready.json",
        run_dir / "ready.json",
        run_dir / "eval_summary.json",
    ]
    for path in candidates:
        if path.exists():
            data = _safe_load_json(path)
            for key in ["READY_TO_SUBMIT", "ready_to_submit", "ready", "gate_passed"]:
                if key in data:
                    return bool(data.get(key)), f"{path.name}:{key}"
    return False, "ready flag not found"


def _extract_qa_summary(run_dir: Path) -> Dict[str, object]:
    data = {}
    candidates = [
        run_dir / "qa_summary.json",
        run_dir / "qa_report.json",
        run_dir / "qa.json",
    ]
    for path in candidates:
        if path.exists():
            data = _safe_load_json(path)
            break
    errors = data.get("error_count") or data.get("errors")
    warnings = data.get("warn_count") or data.get("warnings")
    major = data.get("major_warnings") or []
    return {
        "errors": errors if errors is not None else 0,
        "warnings": warnings if warnings is not None else 0,
        "major_warnings": major,
    }


def _extract_impact_summary(run_dir: Path) -> Dict[str, object]:
    impact_path = run_dir / "impact_summary.json"
    if not impact_path.exists():
        return {"has_impact": False, "details": ""}
    data = _safe_load_json(impact_path)
    return {
        "has_impact": bool(data.get("has_impact", False)),
        "details": data.get("details", ""),
    }


def _extract_metric_from_files(run_dir: Path, filenames: List[str], key: str) -> Optional[object]:
    for name in filenames:
        path = run_dir / name
        if path.exists():
            data = _safe_load_json(path)
            return data.get(key)
    return None


def _safe_load_json(path: Path) -> Dict[str, object]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _build_diff_report(
    submission_version: str,
    artifacts: Dict[str, Optional[Path]],
    previous_package_path: Optional[str],
    run_id: str,
):
    previous_files, temp_dir = _resolve_previous_files(submission_version, previous_package_path, run_id)
    try:
        return generate_diff_report(
            current_docx=artifacts.get("thesis_docx"),
            previous_docx=previous_files.get("thesis_docx"),
            current_md=artifacts.get("report_md"),
            previous_md=previous_files.get("report_md"),
            current_pptx=artifacts.get("slides_pptx"),
            previous_pptx=previous_files.get("slides_pptx"),
        )
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _resolve_previous_files(
    submission_version: str,
    previous_package_path: Optional[str],
    run_id: str,
) -> Tuple[Dict[str, Optional[Path]], Optional[Path]]:
    if previous_package_path:
        previous_path = Path(previous_package_path)
        if previous_path.exists():
            if previous_path.is_file() and previous_path.suffix == ".zip":
                return _extract_from_zip(previous_path)
            if previous_path.is_dir():
                return _discover_artifacts(previous_path), None

    previous_dir = _find_previous_submission_dir(submission_version, run_id)
    if previous_dir:
        return _discover_artifacts(previous_dir), None

    return {"thesis_docx": None, "slides_pptx": None, "report_md": None}, None


def _find_previous_submission_dir(submission_version: str, run_id: str) -> Optional[Path]:
    base_dir = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME
    if not base_dir.exists():
        return None
    versions = []
    for path in base_dir.iterdir():
        if path.is_dir() and path.name != submission_version:
            versions.append(path.name)
    target = _closest_previous_version(submission_version, versions)
    return base_dir / target if target else None


def _closest_previous_version(current: str, versions: List[str]) -> Optional[str]:
    current_key = _version_key(current)
    candidates = [v for v in versions if _version_key(v) < current_key]
    if not candidates:
        return None
    return max(candidates, key=_version_key)


def _version_key(version: str) -> Tuple[int, ...]:
    parts = re.split(r"[._-]", version)
    return tuple(int(part) if part.isdigit() else 0 for part in parts)


def _extract_from_zip(zip_path: Path) -> Tuple[Dict[str, Optional[Path]], Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix="submission_prev_"))
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(temp_dir)
    return _discover_artifacts(temp_dir), temp_dir


def _write_email_draft(folder: Path, draft) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"email_{draft.recipient_type}.txt"
    path = folder / filename
    content = f"Subject: {draft.subject}\n\n{draft.body}"
    path.write_text(content, encoding="utf-8")
    return path


def _write_check_report(json_paths: List[Path], md_paths: List[Path], report: Dict[str, object]) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    lines = ["# Submission Check Report", "", f"Blocked: {report.get('blocked')}", "", "## Checks"]
    for item in report.get("checks", []):
        lines.append(f"- [{item['status']}] {item['title']} ({item['details']})")
    markdown = "\n".join(lines) + "\n"

    for json_path in json_paths:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(payload, encoding="utf-8")
    for md_path in md_paths:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")


def _build_zip(submission_root: Path, submission_version: str, run_id: str, blocked: bool) -> Path:
    base_dir = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME
    suffix = "_BLOCKED" if blocked else ""
    zip_name = f"submission_package_ver{submission_version}{suffix}.zip"
    zip_path = base_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in submission_root.rglob("*"):
            if path.is_file():
                arcname = path.relative_to(submission_root.parent)
                zf.write(path, arcname)

    return zip_path
