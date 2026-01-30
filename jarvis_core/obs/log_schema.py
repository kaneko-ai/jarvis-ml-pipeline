"""Structured logging schema for observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

LEVELS = {"DEBUG", "INFO", "WARN", "ERROR"}
EVENTS = {"step_start", "step_end", "progress", "warning", "error", "info"}


def now_iso() -> str:
    """Return current UTC timestamp in ISO8601."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LogEvent:
    """Structured log event."""

    ts: str
    level: str
    run_id: str
    job_id: str
    component: str
    step: str
    event: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    err: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ts": self.ts,
            "level": self.level,
            "run_id": self.run_id,
            "job_id": self.job_id,
            "component": self.component,
            "step": self.step,
            "event": self.event,
            "message": self.message,
            "data": self.data or {},
        }
        if self.err:
            payload["err"] = self.err
        return payload


def build_log_event(
    *,
    level: str,
    run_id: str,
    job_id: str,
    component: str,
    step: str,
    event: str,
    message: str,
    data: dict[str, Any] | None = None,
    err: dict[str, str] | None = None,
    ts: str | None = None,
) -> LogEvent:
    """Create a structured log event with defaults."""
    normalized_level = level.upper()
    normalized_event = event.lower()
    if normalized_level not in LEVELS:
        normalized_level = "INFO"
    if normalized_event not in EVENTS:
        normalized_event = "info"
    return LogEvent(
        ts=ts or now_iso(),
        level=normalized_level,
        run_id=run_id,
        job_id=job_id,
        component=component,
        step=step,
        event=normalized_event,
        message=message,
        data=data or {},
        err=err,
    )