"""Schedule management endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from jarvis_core.scheduler import engine, idempotency, runner, store
from jarvis_web.auth import verify_token
from jarvis_web import jobs
from jarvis_web.job_runner import run_job


router = APIRouter()


def _schedule_response(schedule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **schedule,
        "next_run_at": engine.next_run_at(schedule),
        "last_run_at": schedule.get("last_run_at"),
        "last_status": schedule.get("last_status"),
        "last_error_summary": schedule.get("last_error_summary"),
    }


@router.get("/api/schedules")
async def list_schedules(_: bool = Depends(verify_token)):
    schedules = store.list_schedules()
    return {"schedules": [_schedule_response(s) for s in schedules]}


@router.post("/api/schedules")
async def create_schedule(payload: Dict[str, Any], _: bool = Depends(verify_token)):
    try:
        schedule = store.save_schedule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _schedule_response(schedule)


@router.get("/api/schedules/{schedule_id}")
async def get_schedule(schedule_id: str, _: bool = Depends(verify_token)):
    schedule = store.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="schedule not found")
    return _schedule_response(schedule)


@router.patch("/api/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, payload: Dict[str, Any], _: bool = Depends(verify_token)):
    schedule = store.update_schedule(schedule_id, payload)
    if not schedule:
        raise HTTPException(status_code=404, detail="schedule not found")
    return _schedule_response(schedule)


@router.post("/api/schedules/{schedule_id}/run")
async def run_schedule(
    schedule_id: str,
    force: Optional[bool] = Query(False),
    _: bool = Depends(verify_token),
):
    schedule = store.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="schedule not found")

    now = datetime.now(timezone.utc)
    idempotency_key = idempotency.idempotency_key(schedule, now)
    if not force:
        existing = store.find_run_by_idempotency(schedule_id, idempotency_key)
        if existing:
            return {"run_id": existing.get("run_id"), "status": existing.get("status"), "skipped": True}

    run = store.create_run(schedule_id, idempotency_key, runner.build_payload(schedule))
    payload = {**run.get("payload", {}), "schedule_run_id": run["run_id"]}
    job = jobs.create_job("collect_and_ingest", payload)
    store.update_run(run["run_id"], job_id=job["job_id"], status="queued")
    jobs.run_in_background(job["job_id"], lambda: run_job(job["job_id"]))
    return {"run_id": run["run_id"], "job_id": job["job_id"], "status": "queued"}


@router.get("/api/schedules/{schedule_id}/history")
async def schedule_history(schedule_id: str, limit: int = 50, _: bool = Depends(verify_token)):
    schedule = store.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="schedule not found")
    return {"schedule_id": schedule_id, "history": store.list_runs(schedule_id, limit=limit)}
