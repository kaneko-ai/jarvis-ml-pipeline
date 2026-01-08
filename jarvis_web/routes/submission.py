from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from jarvis_core.submission import build_submission_package


DATA_RUNS_DIR = Path("data/runs")
SUBMISSION_DIRNAME = "submission"


router = APIRouter()


class SubmissionBuildRequest(BaseModel):
    run_id: str
    submission_version: str
    recipient_type: str
    previous_package_path: Optional[str] = None


@router.post("/api/submission/build")
async def build_submission(request: SubmissionBuildRequest):
    try:
        result = build_submission_package(
            run_id=request.run_id,
            submission_version=request.submission_version,
            recipient_type=request.recipient_type,
            previous_package_path=request.previous_package_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "run_id": result.run_id,
        "submission_version": result.submission_version,
        "blocked": result.blocked,
        "package_path": str(result.package_path),
        "changelog_path": str(result.changelog_path),
        "email_subject": result.email_subject,
        "email_body": result.email_body,
        "check_report_path": str(result.check_report_path),
    }


@router.get("/api/submission/run/{run_id}/latest")
async def get_latest_submission(run_id: str):
    base_dir = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME
    if not base_dir.exists():
        raise HTTPException(status_code=404, detail="No submission data found")

    versions = [p.name for p in base_dir.iterdir() if p.is_dir()]
    if not versions:
        raise HTTPException(status_code=404, detail="No submission versions found")
    latest = max(versions, key=_version_key)
    return {"run_id": run_id, "latest_version": latest}


@router.get("/api/submission/run/{run_id}/download")
async def download_submission(run_id: str, version: str):
    base_dir = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME
    if not base_dir.exists():
        raise HTTPException(status_code=404, detail="No submission data found")

    pattern = f"submission_package_ver{version}"
    matches = list(base_dir.glob(f"{pattern}*.zip"))
    if not matches:
        raise HTTPException(status_code=404, detail="Package not found")
    return FileResponse(matches[0])


@router.get("/api/submission/run/{run_id}/email")
async def get_email_draft(run_id: str, version: str, recipient_type: str):
    draft_path = _email_path(run_id, version, recipient_type)
    if not draft_path.exists():
        raise HTTPException(status_code=404, detail="Email draft not found")
    return PlainTextResponse(draft_path.read_text(encoding="utf-8"))


@router.get("/api/submission/run/{run_id}/changelog")
async def get_changelog(run_id: str, version: str):
    changelog_path = _changelog_path(run_id, version)
    if not changelog_path.exists():
        raise HTTPException(status_code=404, detail="ChangeLog not found")
    return PlainTextResponse(changelog_path.read_text(encoding="utf-8"))


def _version_key(version: str):
    parts = []
    for part in version.replace("-", ".").split("."):
        parts.append(int(part) if part.isdigit() else 0)
    return tuple(parts)


def _email_path(run_id: str, version: str, recipient_type: str) -> Path:
    return (
        DATA_RUNS_DIR
        / run_id
        / SUBMISSION_DIRNAME
        / version
        / "email_drafts"
        / f"email_{recipient_type}.txt"
    )


def _changelog_path(run_id: str, version: str) -> Path:
    base = DATA_RUNS_DIR / run_id / SUBMISSION_DIRNAME / version / "03_reports"
    matches = list(base.glob("*ChangeLog*"))
    return matches[0] if matches else base / "ChangeLog.md"
