"""Lightweight observability hooks for scheduler."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

OBS_DIR = Path("data/obs")
OBS_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_PATH = OBS_DIR / "events.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_event(event_type: str, payload: dict[str, Any]) -> None:
    event = {"timestamp": _now(), "type": event_type, **payload}
    with open(EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def heartbeat(name: str) -> None:
    record_event("heartbeat", {"name": name})


def alert(name: str, severity: str, message: str) -> None:
    record_event("alert", {"name": name, "severity": severity, "message": message})
