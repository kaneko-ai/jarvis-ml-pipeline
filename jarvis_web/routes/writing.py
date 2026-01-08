"""Routes for writing draft generation."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from jarvis_web import jobs
from jarvis_web.job_runner import run_job


router = APIRouter()


class WritingOutputs(BaseModel):
    research_plan: bool = True
    thesis: bool = True
    slides: bool = True
    docx: bool = True
    pptx: bool = True


class WritingRequest(BaseModel):
    run_id: str
    outputs: WritingOutputs


@router.post("/api/writing/generate")
async def generate_writing(request: WritingRequest):
    payload = {
        "run_id": request.run_id,
        "outputs": request.outputs.dict(),
    }
    job = jobs.create_job("writing_generate", payload)
    jobs.run_in_background(job["job_id"], lambda: run_job(job["job_id"]))
    return {"job_id": job["job_id"], "status": job["status"]}


@router.get("/api/writing/run/{run_id}/files")
async def list_writing_files(run_id: str):
    writing_dir = Path("data/runs") / run_id / "writing"
    if not writing_dir.exists():
        return {"files": []}
    files = []
    for path in writing_dir.iterdir():
        if path.is_file():
            files.append({"name": path.name, "size": path.stat().st_size})
    return {"files": files}


@router.get("/api/writing/run/{run_id}/download")
async def download_writing_file(run_id: str, path: str):
    run_dir = Path("data/runs") / run_id
    target = (run_dir / path).resolve()
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if run_dir.resolve() not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
    return FileResponse(target)
