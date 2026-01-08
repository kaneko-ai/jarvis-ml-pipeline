"""Retention management for logs and metrics."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jarvis_core.obs.logger import SYSTEM_LOG_PATH, get_logger
from jarvis_core.obs.metrics import METRICS_PATH

RETENTION_CONFIG = {
    "run_events_days": 30,
    "system_log_days": 14,
    "metrics_raw_days": 30,
    "metrics_rollup_days": 180,
}


def _parse_ts(payload: dict[str, Any]) -> datetime | None:
    ts = payload.get("ts") or payload.get("timestamp")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _prune_jsonl(path: Path, days: int) -> int:
    if not path.exists():
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    kept_lines = []
    removed = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_ts(payload)
            if ts and ts >= cutoff:
                kept_lines.append(line)
            else:
                removed += 1
    if removed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(kept_lines)
    return removed


def run_retention() -> dict[str, int]:
    removed = {
        "run_events": 0,
        "system_log": 0,
        "metrics_raw": 0,
    }
    run_logs_root = Path("data/runs")
    if run_logs_root.exists():
        for log_path in run_logs_root.glob("*/logs/events.jsonl"):
            removed["run_events"] += _prune_jsonl(log_path, RETENTION_CONFIG["run_events_days"])
    removed["system_log"] = _prune_jsonl(SYSTEM_LOG_PATH, RETENTION_CONFIG["system_log_days"])
    removed["metrics_raw"] = _prune_jsonl(METRICS_PATH, RETENTION_CONFIG["metrics_raw_days"])
    logger = get_logger(run_id="system", job_id="retention", component="retention")
    logger.info("retention cleanup complete", data={"removed": removed})
    return removed
