"""Deferred sync queue for ops_extract Drive uploads."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import OPS_EXTRACT_SCHEMA_VERSION


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enqueue_sync_request(
    *,
    queue_dir: Path,
    run_dir: Path,
    run_id: str,
    reason: str,
    drive_folder_id: str | None,
) -> Path:
    queue_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "state": "deferred",
        "reason": reason,
        "drive_folder_id": drive_folder_id or "",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "attempts": 0,
        "last_error": "",
    }
    path = queue_dir / f"{run_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def load_sync_queue(queue_dir: Path) -> list[dict[str, Any]]:
    if not queue_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(queue_dir.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                payload["_path"] = str(path)
                rows.append(payload)
        except Exception:
            continue
    return rows


def mark_sync_queue_state(path: Path, *, state: str, error: str = "", attempts: int | None = None) -> None:
    payload: dict[str, Any] = {}
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                payload = loaded
        except Exception:
            payload = {}
    payload["schema_version"] = payload.get("schema_version", OPS_EXTRACT_SCHEMA_VERSION)
    payload["state"] = state
    payload["last_error"] = error
    payload["updated_at"] = _now_iso()
    if attempts is not None:
        payload["attempts"] = int(attempts)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

