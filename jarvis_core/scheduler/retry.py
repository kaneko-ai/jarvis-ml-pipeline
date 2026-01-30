"""Retry helpers for scheduler runs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def next_retry_at(attempts: int, cooldown_minutes: int) -> str:
    base_seconds = 60
    delay = base_seconds * (2 ** max(attempts - 1, 0))
    cooldown = cooldown_minutes * 60
    wait = max(delay, cooldown)
    return (datetime.now(timezone.utc) + timedelta(seconds=wait)).isoformat()