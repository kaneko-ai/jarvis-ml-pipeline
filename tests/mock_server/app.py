from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FILES_DIR = FIXTURES_DIR / "files"

app = FastAPI(title="JARVIS Mock API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_json(name: str) -> Any:
    path = FIXTURES_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/capabilities")
async def capabilities(request: Request):
    features = {
        "health": True,
        "capabilities": True,
        "runs": True,
        "runs_detail": True,
        "runs_files": True,
        "runs_files_download": True,
        "research_rank": True,
        "qa_report": True,
        "submission_decision": False,
        "finance_forecast": False,
    }
    for key, value in request.query_params.items():
        if key in features:
            features[key] = value.lower() != "false"
    return {"version": "v1", "features": features}


@app.get("/api/runs")
async def list_runs():
    return load_json("runs.json")


@app.get("/api/runs/{run_id}")
async def run_detail(run_id: str):
    path = FIXTURES_DIR / f"run_{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="run not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/runs/{run_id}/files")
async def run_files(run_id: str):
    path = FIXTURES_DIR / f"files_{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="run files not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/runs/{run_id}/files/{path:path}")
async def run_file(run_id: str, path: str):
    file_path = FILES_DIR / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return Response(content=file_path.read_bytes(), media_type="application/octet-stream")


@app.get("/api/research/rank")
async def research_rank():
    return load_json("research_rank.json")


@app.get("/api/qa/report")
async def qa_report():
    return load_json("qa_report.json")


@app.get("/api/submission/decision")
async def submission_decision():
    raise HTTPException(status_code=501, detail="not implemented")


@app.get("/api/finance/forecast")
async def finance_forecast():
    raise HTTPException(status_code=501, detail="not implemented")
