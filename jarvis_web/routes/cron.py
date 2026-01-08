"""Cron tick endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from jarvis_core.obs import heartbeat
from jarvis_core.scheduler import runner, store
from jarvis_web.auth import verify_api_token
from jarvis_web import jobs
from jarvis_web.job_runner import run_job


router = APIRouter()


def _enqueue_job(run_record: dict) -> dict:
    payload = {**run_record.get("payload", {}), "schedule_run_id": run_record["run_id"]}
    job = jobs.create_job("collect_and_ingest", payload)
    store.update_run(
        run_record["run_id"], job_id=job["job_id"], status="queued", next_retry_at=None
    )
    jobs.run_in_background(job["job_id"], lambda: run_job(job["job_id"]))
    return {"run_id": run_record["run_id"], "job_id": job["job_id"], "status": "queued"}


@router.post("/api/cron/tick")
async def cron_tick(_: bool = Depends(verify_api_token)):
    heartbeat("scheduler_cron")
    now = datetime.now(timezone.utc)
    plans = runner.plan_due_runs(now=now)
    queued = [_enqueue_job(plan.run) for plan in plans]

    retries = store.list_due_retries(now=now)
    retried = []
    for run_record in retries:
        retried.append(_enqueue_job(run_record))

    return {
        "timestamp": now.isoformat(),
        "queued": queued,
        "retried": retried,
        "count": len(queued) + len(retried),
    }
