"""Structured logger with run/job context."""

from __future__ import annotations

import json
import threading
import traceback
from pathlib import Path
from typing import Any

from jarvis_core.obs.log_schema import build_log_event

_LOG_LOCK = threading.Lock()
SYSTEM_LOG_PATH = Path("data/ops/system.log.jsonl")


def _run_log_path(run_id: str) -> Path:
    return Path("data/runs") / run_id / "logs" / "events.jsonl"


def _append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_LOCK:
        with open(path, "a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


class ObservabilityLogger:
    """Logger that writes structured JSONL events."""

    def __init__(self, run_id: str, job_id: str, component: str, step: str = "") -> None:
        self.run_id = run_id
        self.job_id = job_id
        self.component = component
        self.step = step

    def _write(
        self,
        *,
        level: str,
        event: str,
        message: str,
        step: str | None = None,
        data: dict[str, Any] | None = None,
        err: dict[str, str] | None = None,
    ) -> None:
        payload = build_log_event(
            level=level,
            run_id=self.run_id,
            job_id=self.job_id,
            component=self.component,
            step=step or self.step,
            event=event,
            message=message,
            data=data,
            err=err,
        ).to_dict()
        _append_jsonl(_run_log_path(self.run_id), [payload])
        _append_jsonl(SYSTEM_LOG_PATH, [payload])

    def info(
        self, message: str, *, step: str | None = None, data: dict[str, Any] | None = None
    ) -> None:
        self._write(level="INFO", event="info", message=message, step=step, data=data)

    def warning(
        self, message: str, *, step: str | None = None, data: dict[str, Any] | None = None
    ) -> None:
        self._write(level="WARN", event="warning", message=message, step=step, data=data)

    def error(
        self,
        message: str,
        *,
        step: str | None = None,
        data: dict[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> None:
        err_payload = None
        if exc:
            err_payload = {
                "type": type(exc).__name__,
                "stack": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            }
        self._write(
            level="ERROR", event="error", message=message, step=step, data=data, err=err_payload
        )

    def step_start(
        self, step: str, message: str = "step start", data: dict[str, Any] | None = None
    ) -> None:
        self._write(level="INFO", event="step_start", message=message, step=step, data=data)

    def step_end(
        self, step: str, message: str = "step end", data: dict[str, Any] | None = None
    ) -> None:
        self._write(level="INFO", event="step_end", message=message, step=step, data=data)

    def progress(self, step: str, percent: int, data: dict[str, Any] | None = None) -> None:
        payload = {"percent": percent}
        if data:
            payload.update(data)
        self._write(
            level="INFO", event="progress", message=f"{step} {percent}%", step=step, data=payload
        )


def get_logger(run_id: str, job_id: str, component: str, step: str = "") -> ObservabilityLogger:
    """Return a structured logger bound to run/job/component."""
    return ObservabilityLogger(run_id=run_id, job_id=job_id, component=component, step=step)


def tail_logs(run_id: str, limit: int = 200) -> list[dict[str, Any]]:
    """Return the last N log entries for a run."""
    path = _run_log_path(run_id)
    if not path.exists() or limit <= 0:
        return []
    with open(path, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    return [json.loads(line) for line in lines[-limit:]]
