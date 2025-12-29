"""Health checks for cron/worker/index state."""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis_web import jobs


WORKER_HEARTBEAT_KEY = "worker:heartbeat"
DEFAULT_HEARTBEAT_TTL_SEC = 120


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis():
    import redis

    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        raise RuntimeError("REDIS_URL is required for health checks")
    return redis.from_url(redis_url)


def update_worker_heartbeat(redis_client, ttl_sec: int = DEFAULT_HEARTBEAT_TTL_SEC) -> None:
    redis_client.set(WORKER_HEARTBEAT_KEY, _now_iso(), ex=ttl_sec)


def start_worker_heartbeat(stop_event: threading.Event, interval_sec: int = 60) -> None:
    try:
        redis_client = get_redis()
    except Exception:
        return

    while not stop_event.is_set():
        try:
            update_worker_heartbeat(redis_client)
        except Exception:
            pass
        stop_event.wait(interval_sec)


def _summarize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": job.get("job_id"),
        "type": job.get("type"),
        "status": job.get("status"),
        "updated_at": job.get("updated_at"),
        "counts": job.get("counts", {}),
        "error": job.get("error"),
        "payload": {
            "dedupe_key": job.get("payload", {}).get("dedupe_key"),
            "source": job.get("payload", {}).get("source"),
        },
    }


def _load_recent_jobs(limit: int = 10) -> List[Dict[str, Any]]:
    if not jobs.JOBS_DIR.exists():
        return []
    job_files = sorted(jobs.JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    summaries = []
    for path in job_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                job = json.load(f)
        except Exception:
            continue
        payload = job.get("payload", {})
        source = payload.get("source") or payload.get("trigger") or payload.get("cron")
        if source not in ("cron", True, "cron-worker"):
            continue
        summaries.append(_summarize_job(job))
        if len(summaries) >= limit:
            break
    return summaries


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def get_health_snapshot() -> Dict[str, Any]:
    warnings: List[str] = []
    redis_ok = False
    worker_heartbeat_ok = False
    heartbeat_value: Optional[str] = None

    try:
        redis_client = get_redis()
        redis_client.ping()
        redis_ok = True
        heartbeat_value = redis_client.get(WORKER_HEARTBEAT_KEY)
        if isinstance(heartbeat_value, bytes):
            heartbeat_value = heartbeat_value.decode("utf-8")
        worker_heartbeat_ok = heartbeat_value is not None
    except Exception as exc:
        warnings.append(f"redis_error: {exc}")

    if not worker_heartbeat_ok:
        warnings.append("worker_heartbeat_missing")

    chunks_path = Path("data/chunks.jsonl")
    chunks_file_exists = chunks_path.exists()
    chunks_line_count = _count_lines(chunks_path) if chunks_file_exists else 0

    from jarvis_core.storage import IndexRegistry

    registry = IndexRegistry("data/index")
    faiss_index_exists = registry.has_index()
    if not faiss_index_exists:
        warnings.append("index_missing")

    return {
        "timestamp": _now_iso(),
        "redis_ok": redis_ok,
        "worker_heartbeat_ok": worker_heartbeat_ok,
        "worker_heartbeat": heartbeat_value,
        "last_cron_jobs": _load_recent_jobs(limit=10),
        "chunks_file_exists": chunks_file_exists,
        "chunks_line_count": chunks_line_count,
        "faiss_index_exists": faiss_index_exists,
        "warnings": warnings,
    }
