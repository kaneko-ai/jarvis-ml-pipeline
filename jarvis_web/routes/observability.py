"""Observability API routes."""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from jarvis_core.obs import metrics
from jarvis_core.obs.alerts import engine as alert_engine
from jarvis_core.obs.logger import tail_logs


router = APIRouter(prefix="/api/obs", tags=["observability"])


def _storage_stats(path: Path) -> Dict[str, Any]:
    usage = shutil.disk_usage(path)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    summary = metrics.get_summary()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cron": {"last_heartbeat": summary.get("last_cron_heartbeat_ts")},
        "queue_depth": summary.get("queue_depth", 0),
        "runs_in_progress": summary.get("runs_in_progress", 0),
        "storage": _storage_stats(Path(".")),
    }


@router.get("/logs")
async def logs(run_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id is required")
    return tail_logs(run_id, limit=limit)


@router.get("/metrics/summary")
async def metrics_summary() -> Dict[str, Any]:
    return metrics.get_summary()


@router.get("/metrics/runs")
async def metrics_runs(days: int = 7) -> List[Dict[str, Any]]:
    return metrics.get_run_metrics(days=days)


@router.get("/metrics/errors/top")
async def metrics_errors_top(days: int = 30) -> List[Dict[str, Any]]:
    return metrics.get_top_errors(days=days)


@router.get("/alerts/rules")
async def alert_rules() -> Dict[str, Any]:
    rules = alert_engine.load_rules()
    return {"rules": [rule.to_dict() for rule in rules]}


@router.post("/alerts/rules")
async def alert_rules_upsert(payload: Dict[str, Any]) -> Dict[str, Any]:
    rules_payload = payload.get("rules")
    if not isinstance(rules_payload, list):
        raise HTTPException(status_code=400, detail="rules must be a list")
    rules = alert_engine.update_rules(rules_payload)
    return {"rules": [rule.to_dict() for rule in rules]}


@router.post("/alerts/test")
async def alert_test() -> Dict[str, Any]:
    return alert_engine.send_test_alert()


@router.post("/alerts/evaluate")
async def alert_evaluate() -> Dict[str, Any]:
    alerts = alert_engine.evaluate_rules()
    return {"alerts": alerts}
