"""Scheduler runner utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from jarvis_core.scheduler import engine, idempotency, locks, store


class RunPlan:
    def __init__(self, schedule: dict[str, Any], run: dict[str, Any]):
        self.schedule = schedule
        self.run = run


def build_payload(schedule: dict[str, Any]) -> dict[str, Any]:
    query = schedule.get("query", {})
    return {
        "query": " ".join(query.get("keywords") or []),
        "max_results": query.get("max_papers", 50),
        "oa_only": query.get("oa_only", True),
        "oa_policy": query.get("oa_policy", "strict"),
        "outputs": schedule.get("outputs", {}),
        "tags": schedule.get("tags", []),
        "origin": "schedule",
        "schedule_id": schedule.get("schedule_id"),
    }


def plan_due_runs(now: datetime | None = None, force: bool = False) -> list[RunPlan]:
    now = now or datetime.now(timezone.utc)
    schedules = store.list_schedules()
    due = engine.due_schedules(schedules, now=now)
    plans: list[RunPlan] = []

    for schedule in due:
        schedule_id = schedule.get("schedule_id")
        if not schedule_id:
            continue
        idempotency_key = idempotency.idempotency_key(schedule, now)
        if not force:
            existing = store.find_run_by_idempotency(schedule_id, idempotency_key)
            if existing:
                continue
        ttl_seconds = int(schedule.get("limits", {}).get("max_runtime_minutes", 60)) * 60
        lock_handle = locks.acquire_schedule_lock(schedule_id, ttl_seconds)
        if not lock_handle:
            continue
        payload = build_payload(schedule)
        run = store.create_run(schedule_id, idempotency_key, payload)
        run["lock_key"] = lock_handle.key
        run["lock_path"] = str(lock_handle.path)
        store.update_run(run["run_id"], lock_key=lock_handle.key, lock_path=str(lock_handle.path))
        lock_handle.release()
        plans.append(RunPlan(schedule, run))
    return plans


def mark_run_running(run_id: str) -> None:
    run = store.update_run(run_id, status="running")
    if run:
        store.update_schedule_status(run["schedule_id"], "running")


def mark_run_finished(run_id: str, status: str, error: str | None = None) -> None:
    run = store.update_run(run_id, status=status, error=error)
    if run:
        store.update_schedule_status(run["schedule_id"], status, error=error)
