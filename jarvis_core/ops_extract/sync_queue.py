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


def mark_sync_queue_state(
    path: Path, *, state: str, error: str = "", attempts: int | None = None
) -> None:
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


def _parse_iso(value: str) -> datetime | None:
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def queue_summary(queue_dir: Path) -> dict[str, Any]:
    items = load_sync_queue(queue_dir)
    pending_states = {"pending", "deferred", "in_progress"}
    human_action_states = {"failed", "human_action_required"}
    pending_count = 0
    human_action_required_count = 0
    oldest: datetime | None = None

    for item in items:
        state = str(item.get("state", "")).strip()
        if state in pending_states:
            pending_count += 1
        if state in human_action_states:
            human_action_required_count += 1
        created_at = _parse_iso(str(item.get("created_at", "")))
        if created_at is None:
            continue
        if oldest is None or created_at < oldest:
            oldest = created_at

    oldest_age_days = 0
    if oldest is not None:
        now = datetime.now(timezone.utc)
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=timezone.utc)
        delta_days = (now - oldest).total_seconds() / 86400.0
        oldest_age_days = max(0, int(delta_days))

    return {
        "pending_count": pending_count,
        "oldest_age_days": oldest_age_days,
        "human_action_required_count": human_action_required_count,
    }
