"""Job utilities for background processing."""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


JOBS_DIR = Path("data/jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)

_job_lock = threading.Lock()
_event_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=2)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def _events_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.events.jsonl"


def generate_job_id() -> str:
    return f"job_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"


def create_job(job_type: str, payload: Dict[str, Any], job_id: Optional[str] = None) -> Dict[str, Any]:
    job_id = job_id or generate_job_id()
    job = {
        "job_id": job_id,
        "type": job_type,
        "status": "queued",
        "progress": 0,
        "step": "collect",
        "counts": {
            "found": 0,
            "downloaded": 0,
            "extracted": 0,
            "chunked": 0,
            "indexed": 0,
            "deduped": 0,
            "canonical_papers": 0,
            "claims": 0,
            "failed": 0,
        },
        "payload": payload,
        "started_at": None,
        "updated_at": _now(),
        "error": None,
    }
    _write_job(job)
    append_event(job_id, {"message": "job queued", "level": "info"})
    return job


def read_job(job_id: str) -> Dict[str, Any]:
    job_path = _job_path(job_id)
    if not job_path.exists():
        raise FileNotFoundError(f"Job {job_id} not found")
    with open(job_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_job(job: Dict[str, Any]) -> None:
    job["updated_at"] = _now()
    with _job_lock:
        _job_path(job["job_id"]).parent.mkdir(parents=True, exist_ok=True)
        with open(_job_path(job["job_id"]), "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=2)


def update_job(job_id: str, **changes: Any) -> Dict[str, Any]:
    job = read_job(job_id)
    job.update(changes)
    _write_job(job)
    return job


def set_status(job_id: str, status: str) -> Dict[str, Any]:
    job = read_job(job_id)
    if status == "running" and not job.get("started_at"):
        job["started_at"] = _now()
    job["status"] = status
    _write_job(job)
    append_event(job_id, {"message": f"status -> {status}", "level": "info"})
    return job


def set_step(job_id: str, step: str) -> Dict[str, Any]:
    job = update_job(job_id, step=step)
    append_event(job_id, {"message": f"step -> {step}", "level": "info"})
    return job


def set_progress(job_id: str, progress: int) -> Dict[str, Any]:
    job = read_job(job_id)
    current = job.get("progress", 0)
    job["progress"] = max(current, min(progress, 100))
    _write_job(job)
    return job


def inc_counts(job_id: str, **increments: int) -> Dict[str, Any]:
    job = read_job(job_id)
    counts = job.get("counts", {})
    for key, value in increments.items():
        counts[key] = counts.get(key, 0) + value
    job["counts"] = counts
    _write_job(job)
    return job


def set_error(job_id: str, error: str) -> Dict[str, Any]:
    job = update_job(job_id, error=error)
    append_event(job_id, {"message": error, "level": "error"})
    return job


def append_event(job_id: str, event: Dict[str, Any]) -> None:
    payload = {
        "timestamp": _now(),
        **event,
    }
    with _event_lock:
        _events_path(job_id).parent.mkdir(parents=True, exist_ok=True)
        with open(_events_path(job_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def tail_events(job_id: str, tail: int = 200) -> List[Dict[str, Any]]:
    events_path = _events_path(job_id)
    if not events_path.exists():
        return []
    with open(events_path, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    if tail <= 0:
        return []
    return [json.loads(line) for line in lines[-tail:]]


def run_in_background(job_id: str, fn: Callable[[], None]) -> None:
    def wrapper():
        try:
            fn()
        except Exception as exc:  # pragma: no cover - safety net
            set_error(job_id, f"{type(exc).__name__}: {exc}")
            set_status(job_id, "failed")

    _executor.submit(wrapper)
