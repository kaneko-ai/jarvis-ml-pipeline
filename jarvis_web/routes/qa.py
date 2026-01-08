"""QA API routes for lint/report/ready status."""

from __future__ import annotations

from pathlib import Path
from typing import List
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jarvis_core.style import run_qa_gate

router = APIRouter(prefix="/api/qa", tags=["qa"])


class QALintRequest(BaseModel):
    run_id: str
    targets: List[str] = ["md", "docx", "pptx"]


@router.post("/lint")
async def lint(request: QALintRequest):
    run_dir = Path("logs/runs") / request.run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    qa_result = run_qa_gate(run_id=request.run_id, run_dir=run_dir, targets=request.targets)
    return {
        "issues": qa_result.get("issues", []),
        "ready_to_submit": qa_result.get("ready_to_submit"),
    }


@router.get("/report")
async def report(run_id: str):
    qa_path = Path("data/runs") / run_id / "qa" / "qa_report.json"
    if not qa_path.exists():
        qa_path = Path("logs/runs") / run_id / "qa" / "qa_report.json"
    if not qa_path.exists():
        raise HTTPException(status_code=404, detail="QA report not found")
    return json.loads(qa_path.read_text(encoding="utf-8"))


@router.get("/ready")
async def ready(run_id: str):
    qa_path = Path("data/runs") / run_id / "qa" / "qa_report.json"
    if not qa_path.exists():
        qa_path = Path("logs/runs") / run_id / "qa" / "qa_report.json"
    if not qa_path.exists():
        raise HTTPException(status_code=404, detail="QA report not found")
    data = json.loads(qa_path.read_text(encoding="utf-8"))
    return {"ready_to_submit": data.get("ready_to_submit", False)}
