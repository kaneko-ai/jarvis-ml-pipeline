"""JSONL Telemetry Logger.

Per RP-02, this provides robust logging to events.jsonl.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from .schema import TelemetryEvent


class JsonlTelemetryLogger:
    """Thread-safe JSONL telemetry logger.

    Writes to logs/runs/{run_id}/events.jsonl with robust error handling.
    """

    def __init__(self, run_id: str, logs_dir: str = "logs/runs"):
        self.run_id = run_id
        self.logs_dir = Path(logs_dir)
        self.run_dir = self.logs_dir / run_id
        self.events_file = self.run_dir / "events.jsonl"
        self._lock = threading.Lock()
        self._step_counter = 0

        # Ensure directory exists
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def _next_step(self) -> int:
        """Get next step ID (thread-safe)."""
        with self._lock:
            self._step_counter += 1
            return self._step_counter

    def log(self, event: TelemetryEvent) -> None:
        """Log a telemetry event."""
        try:
            with self._lock:
                with open(self.events_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            # Don't crash on logging failures
            print(f"[TELEMETRY ERROR] Failed to log event: {e}")

    def log_event(
        self,
        event: str,
        event_type: str,
        trace_id: str,
        level: str = "INFO",
        **kwargs,
    ) -> TelemetryEvent:
        """Convenience method to create and log an event."""
        step_id = self._next_step()

        evt = TelemetryEvent.create(
            run_id=self.run_id,
            trace_id=trace_id,
            step_id=step_id,
            event=event,
            event_type=event_type,
            level=level,
            **kwargs,
        )

        self.log(evt)
        return evt

    def flush(self) -> None:
        """Flush any buffered events (no-op for file-per-event)."""
        pass

    def close(self) -> None:
        """Close the logger."""
        self.flush()


# Global logger instance
_global_logger: JsonlTelemetryLogger | None = None


def init_logger(run_id: str, logs_dir: str = "logs/runs") -> JsonlTelemetryLogger:
    """Initialize global logger for a run."""
    global _global_logger
    _global_logger = JsonlTelemetryLogger(run_id, logs_dir)
    return _global_logger


def get_logger() -> JsonlTelemetryLogger | None:
    """Get global logger if initialized."""
    return _global_logger
