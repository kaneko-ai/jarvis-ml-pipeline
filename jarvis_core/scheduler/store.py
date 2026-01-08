"""Schedule store using JSON files."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from jarvis_core.scheduler.schema import normalize_schedule_payload, validate_required_fields

SCHEDULES_DIR = Path("data/schedules")
RUNS_DIR = SCHEDULES_DIR / "runs"
SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

_index_lock = threading.Lock()
_runs_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _schedule_path(schedule_id: str) -> Path:
    return SCHEDULES_DIR / f"{schedule_id}.json"


def _run_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.json"


def _history_path(schedule_id: str) -> Path:
    return RUNS_DIR / f"{schedule_id}.jsonl"


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def list_schedules() -> list[dict[str, Any]]:
    schedules: list[dict[str, Any]] = []
    with _index_lock:
        for path in sorted(SCHEDULES_DIR.glob("SCH_*.json")):
            schedules.append(_load_json(path))
    return schedules


def get_schedule(schedule_id: str) -> dict[str, Any] | None:
    path = _schedule_path(schedule_id)
    if not path.exists():
        return None
    return _load_json(path)


def save_schedule(payload: dict[str, Any], schedule_id: str | None = None) -> dict[str, Any]:
    validate_required_fields(payload)
    schedule_id = schedule_id or payload.get("schedule_id") or f"SCH_{uuid4().hex[:8]}"
    existing = get_schedule(schedule_id)
    schedule = normalize_schedule_payload(payload, schedule_id, existing)
    with _index_lock:
        _write_json_atomic(_schedule_path(schedule_id), schedule)
    return schedule


def update_schedule(schedule_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_schedule(schedule_id)
    if not existing:
        return None
    payload = {**existing, **patch}
    schedule = normalize_schedule_payload(payload, schedule_id, existing)
    with _index_lock:
        _write_json_atomic(_schedule_path(schedule_id), schedule)
    return schedule


def create_run(schedule_id: str, idempotency_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
    run = {
        "run_id": run_id,
        "schedule_id": schedule_id,
        "status": "queued",
        "idempotency_key": idempotency_key,
        "payload": payload,
        "attempts": 0,
        "created_at": _now(),
        "updated_at": _now(),
        "next_retry_at": None,
        "error": None,
        "job_id": None,
    }
    with _runs_lock:
        _write_json_atomic(_run_path(run_id), run)
        history_path = _history_path(schedule_id)
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"run_id": run_id, "idempotency_key": idempotency_key}, ensure_ascii=False) + "\n")
    return run


def read_run(run_id: str) -> dict[str, Any] | None:
    path = _run_path(run_id)
    if not path.exists():
        return None
    return _load_json(path)


def update_run(run_id: str, **changes: Any) -> dict[str, Any] | None:
    run = read_run(run_id)
    if not run:
        return None
    run.update(changes)
    run["updated_at"] = _now()
    with _runs_lock:
        _write_json_atomic(_run_path(run_id), run)
    return run


def list_runs(schedule_id: str, limit: int = 50) -> list[dict[str, Any]]:
    history_path = _history_path(schedule_id)
    if not history_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with open(history_path, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    for line in lines[-limit:]:
        entry = json.loads(line)
        run = read_run(entry.get("run_id", ""))
        if run:
            entries.append(run)
    return entries


def list_all_runs(limit: int = 50, statuses: list[str] | None = None) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    paths = sorted(RUNS_DIR.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths[:limit]:
        run = _load_json(path)
        if statuses and run.get("status") not in statuses:
            continue
        runs.append(run)
    return runs


def find_run_by_idempotency(schedule_id: str, idempotency_key: str) -> dict[str, Any] | None:
    history_path = _history_path(schedule_id)
    if not history_path.exists():
        return None
    with open(history_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("idempotency_key") == idempotency_key:
                return read_run(entry.get("run_id", ""))
    return None


def list_due_retries(now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    due: list[dict[str, Any]] = []
    with _runs_lock:
        for path in RUNS_DIR.glob("run_*.json"):
            run = _load_json(path)
            if run.get("status") != "failed":
                continue
            next_retry = run.get("next_retry_at")
            if not next_retry:
                continue
            try:
                retry_dt = datetime.fromisoformat(next_retry)
            except ValueError:
                continue
            if retry_dt <= now:
                due.append(run)
    return due


def update_schedule_status(schedule_id: str, status: str, error: str | None = None) -> None:
    schedule = get_schedule(schedule_id)
    if not schedule:
        return
    schedule["last_run_at"] = _now()
    schedule["last_status"] = status
    schedule["last_error_summary"] = error
    schedule["updated_at"] = _now()
    with _index_lock:
        _write_json_atomic(_schedule_path(schedule_id), schedule)
