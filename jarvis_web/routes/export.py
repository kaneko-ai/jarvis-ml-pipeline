"""Export routes for run artifacts."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, PlainTextResponse

from jarvis_core.export.package_builder import build_run_package
from jarvis_web.auth import verify_token


RUNS_OUTPUT_DIR = Path("data/runs")
SOURCE_RUNS_DIR = Path("logs/runs")

router = APIRouter(prefix="/api/export", tags=["export"])


def _ensure_run_output(run_id: str) -> Path:
    run_output = RUNS_OUTPUT_DIR / run_id
    if not run_output.exists():
        if not (SOURCE_RUNS_DIR / run_id).exists():
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        build_run_package(run_id)
    return run_output


@router.get("/run/{run_id}/package")
async def download_package(run_id: str, _: bool = Depends(verify_token)):
    run_output = _ensure_run_output(run_id)
    zip_path = run_output / "export" / f"jarvis_run_{run_id}.zip"
    if not zip_path.exists():
        build_run_package(run_id)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Package not available")
    return FileResponse(zip_path)


@router.get("/run/{run_id}/notes")
async def download_notes(run_id: str, _: bool = Depends(verify_token)):
    run_output = _ensure_run_output(run_id)
    notes_dir = run_output / "notes"
    if not notes_dir.exists():
        build_run_package(run_id)
    if not notes_dir.exists():
        raise HTTPException(status_code=404, detail="Notes not available")
    zip_path = run_output / "export" / f"notes_{run_id}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    from jarvis_core.export.package_builder import _zip_dir

    _zip_dir(notes_dir, zip_path)
    return FileResponse(zip_path)


@router.get("/run/{run_id}/notebooklm")
async def download_notebooklm(run_id: str, _: bool = Depends(verify_token)):
    run_output = _ensure_run_output(run_id)
    notebook_dir = run_output / "notebooklm"
    if not notebook_dir.exists():
        build_run_package(run_id, generate_notebooklm=True)
    if not notebook_dir.exists():
        raise HTTPException(status_code=404, detail="NotebookLM assets not available")
    zip_path = run_output / "export" / f"notebooklm_{run_id}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    from jarvis_core.export.package_builder import _zip_dir

    _zip_dir(notebook_dir, zip_path)
    return FileResponse(zip_path)


@router.get("/run/{run_id}/notebooklm/prompt/{prompt_name}")
async def get_notebooklm_prompt(
    run_id: str,
    prompt_name: str,
    _: bool = Depends(verify_token),
):
    run_output = _ensure_run_output(run_id)
    notebook_dir = run_output / "notebooklm"
    if not notebook_dir.exists():
        build_run_package(run_id, generate_notebooklm=True)
    filename_map = {
        "podcast_prompt_1paper": "podcast_prompt_1paper.txt",
        "podcast_prompt_3to5papers": "podcast_prompt_3to5papers.txt",
        "podcast_script_outline": "podcast_script_outline.md",
    }
    filename = filename_map.get(prompt_name)
    if not filename:
        raise HTTPException(status_code=400, detail="Unknown prompt name")
    prompt_path = notebook_dir / filename
    if not prompt_path.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    return PlainTextResponse(prompt_path.read_text(encoding="utf-8"))
