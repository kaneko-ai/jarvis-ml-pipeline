"""Decision Intelligence API routes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from jarvis_core.decision.elicitation import template_payload, validate_payload
from jarvis_core.decision.model import evaluate_options
from jarvis_core.decision.report import write_report_files
from jarvis_core.export.package_builder import build_decision_package
from jarvis_core.decision.schema import DecisionComparison

router = APIRouter()

REPORTS_DIR = Path("logs/decision_reports")
LATEST_REPORT_DIR = REPORTS_DIR / "latest"


class DecisionRequest(BaseModel):
    """Request payload for decision simulation."""

    options: list
    assumptions: list
    user_constraints: Optional[Dict[str, object]] = None


class ReportRequest(BaseModel):
    """Request payload for report generation."""

    comparison: DecisionComparison


@router.get("/templates")
async def get_templates():
    """Return template payload for decision inputs."""
    return template_payload()


@router.post("/simulate")
async def simulate_decision(payload: Dict[str, object]):
    """Simulate decision outcomes."""
    validation = validate_payload(payload)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={"errors": validation["errors"]})

    parsed = validation["parsed"]
    comparison = evaluate_options(parsed.options, parsed.assumptions)
    return comparison.dict()


@router.post("/report")
async def generate_report(request: ReportRequest):
    """Generate decision report files."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_dir = REPORTS_DIR / timestamp
    files = write_report_files(request.comparison, report_dir)

    LATEST_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files.values():
        target = LATEST_REPORT_DIR / path.name
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "report_dir": str(report_dir),
        "files": {name: str(path) for name, path in files.items()},
        "disclaimer": request.comparison.disclaimer,
    }


@router.get("/download")
async def download_report(format: str = "zip"):
    """Download the latest decision report package."""
    if format != "zip":
        raise HTTPException(status_code=400, detail="Only zip format is supported")

    md_path = LATEST_REPORT_DIR / "decision_report.md"
    html_path = LATEST_REPORT_DIR / "decision_report.html"

    if not md_path.exists() or not html_path.exists():
        raise HTTPException(status_code=404, detail="No report available")

    zip_path = build_decision_package({"markdown": md_path, "html": html_path}, LATEST_REPORT_DIR)
    return FileResponse(zip_path, filename=zip_path.name, media_type="application/zip")
