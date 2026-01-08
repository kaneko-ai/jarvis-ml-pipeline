"""Structured Run Trace.

Per V4-P05, this provides workflow execution tracing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TraceStep:
    """A single step in workflow execution."""

    step_id: str
    name: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str = "running"  # running, success, failed
    artifact_id: str | None = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "artifact_id": self.artifact_id,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    @property
    def duration_ms(self) -> int | None:
        if self.ended_at and self.started_at:
            return int((self.ended_at - self.started_at).total_seconds() * 1000)
        return None


class RunTrace:
    """Execution trace for a workflow run."""

    def __init__(self, workflow: str, run_id: str = None):
        self.workflow = workflow
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.started_at = datetime.now()
        self.ended_at: datetime | None = None
        self.steps: list[TraceStep] = []
        self.status = "running"
        self._step_counter = 0

    def start_step(self, name: str, metadata: dict = None) -> str:
        """Start a new trace step."""
        self._step_counter += 1
        step_id = f"step_{self._step_counter}"

        step = TraceStep(
            step_id=step_id,
            name=name,
            started_at=datetime.now(),
            metadata=metadata or {},
        )
        self.steps.append(step)
        return step_id

    def end_step(
        self,
        step_id: str,
        status: str = "success",
        artifact_id: str = None,
        error: str = None,
    ) -> None:
        """End a trace step."""
        for step in self.steps:
            if step.step_id == step_id:
                step.ended_at = datetime.now()
                step.status = status
                step.artifact_id = artifact_id
                step.error = error
                break

    def finish(self, status: str = "success") -> None:
        """Finish the trace."""
        self.ended_at = datetime.now()
        self.status = status

        # Mark any running steps as failed
        for step in self.steps:
            if step.status == "running":
                step.status = "aborted"
                step.ended_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "workflow": self.workflow,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "steps": [s.to_dict() for s in self.steps],
        }

    @property
    def duration_ms(self) -> int | None:
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds() * 1000)
        return None

    def save(self, output_dir: str) -> str:
        """Save trace to file."""
        path = Path(output_dir) / "workflows"
        path.mkdir(parents=True, exist_ok=True)

        trace_file = path / "run_trace.json"
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        return str(trace_file)


# Global trace for current run
_current_trace: RunTrace | None = None


def start_trace(workflow: str) -> RunTrace:
    """Start a new global trace."""
    global _current_trace
    _current_trace = RunTrace(workflow)
    return _current_trace


def get_current_trace() -> RunTrace | None:
    """Get current trace."""
    return _current_trace


def trace_step(name: str, metadata: dict = None):
    """Decorator to trace a function as a step."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            trace = get_current_trace()
            step_id = trace.start_step(name, metadata) if trace else None
            try:
                result = func(*args, **kwargs)
                if trace:
                    trace.end_step(step_id, "success")
                return result
            except Exception as e:
                if trace:
                    trace.end_step(step_id, "failed", error=str(e))
                raise

        return wrapper

    return decorator
