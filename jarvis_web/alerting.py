"""Webhook alerting utilities."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict


LEVEL_ORDER = {
    "debug": 10,
    "info": 20,
    "warning": 30,
    "error": 40,
}


def _should_send(level: str) -> bool:
    configured = os.environ.get("ALERT_LEVEL", "error").lower().strip()
    return LEVEL_ORDER.get(level, 100) >= LEVEL_ORDER.get(configured, 40)


def send_webhook(payload: Dict[str, Any], level: str = "error") -> bool:
    url = os.environ.get("ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return False
    if not _should_send(level):
        return False

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
        return True
    except Exception:
        return False


def alert_event(event: str, detail: Dict[str, Any], level: str = "error") -> bool:
    payload = {
        "event": event,
        "level": level,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **detail,
    }
    return send_webhook(payload, level=level)
