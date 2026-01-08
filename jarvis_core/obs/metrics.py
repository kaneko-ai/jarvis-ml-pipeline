"""Metrics collection and aggregation for observability."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_METRICS_LOCK = threading.Lock()
OPS_DIR = Path("data/ops")
METRICS_PATH = OPS_DIR / "metrics.jsonl"
CRON_HEARTBEAT_PATH = OPS_DIR / "cron_heartbeat.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _append_metric(event: dict[str, Any]) -> None:
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"ts": _now(), **event}
    with _METRICS_LOCK:
        with open(METRICS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def record_run_start(run_id: str, job_id: str, component: str) -> None:
    _append_metric(
        {
            "type": "run_start",
            "run_id": run_id,
            "job_id": job_id,
            "component": component,
        }
    )


def record_run_end(
    run_id: str,
    job_id: str,
    status: str,
    duration_ms: float,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    _append_metric(
        {
            "type": "run_end",
            "run_id": run_id,
            "job_id": job_id,
            "status": status,
            "duration_ms": duration_ms,
            "error_type": error_type,
            "error_message": error_message,
        }
    )


def record_step_duration(run_id: str, step: str, duration_ms: float) -> None:
    _append_metric(
        {
            "type": "step_end",
            "run_id": run_id,
            "step": step,
            "duration_ms": duration_ms,
        }
    )


def record_progress(run_id: str, step: str, percent: int) -> None:
    _append_metric(
        {
            "type": "progress",
            "run_id": run_id,
            "step": step,
            "percent": percent,
        }
    )


def record_counts(run_id: str, counts: dict[str, Any]) -> None:
    _append_metric(
        {
            "type": "counts",
            "run_id": run_id,
            "counts": counts,
        }
    )


def record_cron_heartbeat() -> None:
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"ts": _now()}
    with open(CRON_HEARTBEAT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    _append_metric({"type": "cron_heartbeat"})


def _load_metrics_since(days: int) -> list[dict[str, Any]]:
    if not METRICS_PATH.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with open(METRICS_PATH, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    events = []
    for line in lines:
        payload = json.loads(line)
        ts = _parse_ts(payload.get("ts", ""))
        if ts and ts >= cutoff:
            events.append(payload)
    return events


def _load_latest_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        if event.get("type") == "counts":
            for key, value in event.get("counts", {}).items():
                counts[key] = counts.get(key, 0) + int(value or 0)
    return counts


def _read_jobs() -> list[dict[str, Any]]:
    jobs_dir = Path("data/jobs")
    if not jobs_dir.exists():
        return []
    jobs = []
    for path in jobs_dir.glob("job_*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                jobs.append(json.load(f))
        except json.JSONDecodeError:
            continue
    return jobs


def get_summary() -> dict[str, Any]:
    events_24h = _load_metrics_since(1)
    events_7d = _load_metrics_since(7)
    run_events = [e for e in events_7d if e.get("type") == "run_end"]

    runs_total = len(run_events)
    runs_success = sum(1 for e in run_events if e.get("status") == "success")
    runs_failed = sum(1 for e in run_events if e.get("status") == "failed")

    jobs = _read_jobs()
    runs_in_progress = sum(1 for job in jobs if job.get("status") == "running")
    queue_depth = sum(1 for job in jobs if job.get("status") == "queued")

    durations_by_step: dict[str, list[float]] = {}
    for event in events_7d:
        if event.get("type") == "step_end":
            step = event.get("step", "unknown")
            durations_by_step.setdefault(step, []).append(float(event.get("duration_ms", 0)))
    avg_duration_by_step = {
        step: (sum(values) / len(values)) if values else 0
        for step, values in durations_by_step.items()
    }

    counts = _load_latest_counts(events_24h)

    heartbeat = None
    if CRON_HEARTBEAT_PATH.exists():
        try:
            with open(CRON_HEARTBEAT_PATH, encoding="utf-8") as f:
                heartbeat = json.load(f).get("ts")
        except json.JSONDecodeError:
            heartbeat = None

    return {
        "window": {"hours": 24, "days": 7},
        "runs_total": runs_total,
        "runs_success": runs_success,
        "runs_failed": runs_failed,
        "runs_in_progress": runs_in_progress,
        "avg_duration_by_step": avg_duration_by_step,
        "queue_depth": queue_depth,
        "counts": counts,
        "qa_not_ready_count": counts.get("qa_not_ready_count", 0),
        "submission_blocked_count": counts.get("submission_blocked_count", 0),
        "last_cron_heartbeat_ts": heartbeat,
    }


def get_run_metrics(days: int = 7) -> list[dict[str, Any]]:
    events = _load_metrics_since(days)
    return [e for e in events if e.get("type") == "run_end"]


def get_counts_events(days: int = 7) -> list[dict[str, Any]]:
    events = _load_metrics_since(days)
    return [e for e in events if e.get("type") == "counts"]


def get_top_errors(days: int = 30, limit: int = 5) -> list[dict[str, Any]]:
    events = _load_metrics_since(days)
    errors: dict[str, int] = {}
    for event in events:
        if event.get("type") == "run_end" and event.get("status") == "failed":
            label = event.get("error_type") or "UnknownError"
            errors[label] = errors.get(label, 0) + 1
    sorted_errors = sorted(errors.items(), key=lambda item: item[1], reverse=True)
    return [
        {"error_type": error_type, "count": count} for error_type, count in sorted_errors[:limit]
    ]
