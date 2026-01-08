"""Queue management endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from jarvis_core.scheduler import store
from jarvis_web.auth import verify_token


router = APIRouter()


@router.get("/api/queue")
async def list_queue(
    status: Optional[str] = None, limit: int = 50, _: bool = Depends(verify_token)
):
    statuses = [status] if status else None
    runs = store.list_all_runs(limit=limit, statuses=statuses)
    return {"runs": runs, "total": len(runs)}


@router.post("/api/queue/{run_id}/retry")
async def retry_run(run_id: str, _: bool = Depends(verify_token)):
    run = store.read_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    store.update_run(run_id, status="failed", next_retry_at=datetime.now(timezone.utc).isoformat())
    return {"run_id": run_id, "status": "scheduled"}


@router.post("/api/queue/{run_id}/cancel")
async def cancel_run(run_id: str, _: bool = Depends(verify_token)):
    run = store.read_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    store.update_run(run_id, status="cancelled")
    return {"run_id": run_id, "status": "cancelled"}
