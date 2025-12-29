"""Index admin endpoints for retrieval v2."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from jarvis_core.retrieval.indexer import RetrievalIndexer


router = APIRouter()


def verify_admin_token(authorization: Optional[str] = Header(None)) -> bool:
    expected = os.environ.get("JARVIS_WEB_TOKEN", "")
    if not expected:
        return True
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


def _job_path() -> Path:
    return Path("data/index/v2/rebuild_job.json")


def _write_job(status: str, detail: str = "") -> None:
    job = {
        "status": status,
        "detail": detail,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path = _job_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)


def _rebuild_job() -> None:
    _write_job("running")
    try:
        indexer = RetrievalIndexer()
        indexer.rebuild()
        _write_job("completed")
    except Exception as exc:
        _write_job("failed", detail=str(exc))


@router.get("/api/index/v2/status")
async def index_status():
    manifest_path = Path("data/index/v2/manifest.json")
    if not manifest_path.exists():
        return JSONResponse({"available": False, "status": "missing"}, status_code=200)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        manifest = {}
    job_info = {}
    job_path = _job_path()
    if job_path.exists():
        try:
            job_info = json.loads(job_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            job_info = {"status": "unknown"}
    return JSONResponse({"available": True, "manifest": manifest, "job": job_info}, status_code=200)


@router.post("/api/index/v2/update")
async def index_update(_: Dict[str, Any] = Body(default={}), _: bool = Depends(verify_admin_token)):
    try:
        indexer = RetrievalIndexer()
        manifest = indexer.update()
    except Exception as exc:
        return JSONResponse({"status": "error", "detail": str(exc)}, status_code=200)
    return JSONResponse({"status": "ok", "manifest": manifest.to_dict()}, status_code=200)


@router.post("/api/index/v2/rebuild")
async def index_rebuild(_: Dict[str, Any] = Body(default={}), _: bool = Depends(verify_admin_token)):
    thread = threading.Thread(target=_rebuild_job, daemon=True)
    thread.start()
    return JSONResponse({"status": "queued"}, status_code=202)
