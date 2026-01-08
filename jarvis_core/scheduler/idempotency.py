"""Idempotency helpers for schedules."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo


def _parse_freq(rrule: str) -> str:
    for part in rrule.split(";"):
        if part.startswith("FREQ="):
            return part.split("=", 1)[1].upper()
    return "DAILY"


def _period_start(now: datetime, freq: str) -> datetime:
    if freq == "WEEKLY":
        return now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=now.weekday()
        )
    if freq == "MONTHLY":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def query_fingerprint(query: dict[str, Any]) -> str:
    payload = json.dumps(query, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def idempotency_key(schedule: dict[str, Any], now: datetime) -> str:
    freq = _parse_freq(schedule.get("rrule", ""))
    tz_name = schedule.get("timezone", "UTC")
    try:
        tzinfo = ZoneInfo(tz_name)
    except Exception:
        tzinfo = None
    localized = now.astimezone(tzinfo) if tzinfo else now
    period = _period_start(localized, freq)
    fingerprint = query_fingerprint(schedule.get("query", {}))
    raw = f"{schedule.get('schedule_id')}|{period.isoformat()}|{fingerprint}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
