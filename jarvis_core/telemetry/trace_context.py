"""TraceContext.

Per RP-143, provides mandatory trace context for all tool events.
"""

from __future__ import annotations

import threading
import uuid
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class TraceContext:
    """Trace context for event correlation."""

    run_id: str
    trace_id: str
    step_id: int
    parent_step_id: int | None = None
    tool_name: str | None = None

    def with_step(self, step_id: int) -> TraceContext:
        """Create new context with incremented step."""
        return TraceContext(
            run_id=self.run_id,
            trace_id=self.trace_id,
            step_id=step_id,
            parent_step_id=self.step_id,
            tool_name=self.tool_name,
        )

    def with_tool(self, tool_name: str) -> TraceContext:
        """Create new context for a tool call."""
        return TraceContext(
            run_id=self.run_id,
            trace_id=self.trace_id,
            step_id=self.step_id,
            parent_step_id=self.parent_step_id,
            tool_name=tool_name,
        )

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "step_id": self.step_id,
            "parent_step_id": self.parent_step_id,
            "tool_name": self.tool_name,
        }

    @classmethod
    def create(cls, run_id: str | None = None) -> TraceContext:
        """Create new trace context."""
        return cls(
            run_id=run_id or str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            step_id=0,
        )


# Context variable for current trace
_current_context: ContextVar[TraceContext | None] = ContextVar("trace_context", default=None)


def get_current_context() -> TraceContext | None:
    """Get current trace context."""
    return _current_context.get()


def set_current_context(ctx: TraceContext) -> None:
    """Set current trace context."""
    _current_context.set(ctx)


def require_context() -> TraceContext:
    """Require trace context, raise if not set."""
    ctx = get_current_context()
    if ctx is None:
        raise RuntimeError(
            "TraceContext required but not set. " "Ensure run_task or entry point sets context."
        )
    return ctx


class TraceContextManager:
    """Manager for trace context lifecycle."""

    def __init__(self, run_id: str | None = None):
        self.context = TraceContext.create(run_id)
        self._step_counter = 0
        self._lock = threading.Lock()

    def next_step(self) -> TraceContext:
        """Get context for next step."""
        with self._lock:
            self._step_counter += 1
            return self.context.with_step(self._step_counter)

    def enter_tool(self, tool_name: str) -> TraceContext:
        """Enter a tool call."""
        ctx = self.next_step()
        return ctx.with_tool(tool_name)

    def __enter__(self):
        set_current_context(self.context)
        return self

    def __exit__(self, *args):
        _current_context.set(None)


def trace_tool(tool_name: str):
    """Decorator to add trace context to tool functions."""

    def decorator(fn):
        def wrapper(*args, **kwargs):
            ctx = get_current_context()
            if ctx:
                ctx = ctx.with_tool(tool_name)
                set_current_context(ctx)
            return fn(*args, **kwargs)

        return wrapper

    return decorator