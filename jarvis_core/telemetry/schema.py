"""Telemetry Event Schema.

Per RP-02, this defines the structure for ATS-compatible telemetry events.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class EventType(Enum):
    """ATS-compatible event types."""

    COGNITIVE = "COGNITIVE"       # 推論/判断
    ACTION = "ACTION"             # ツール呼び出し
    COORDINATION = "COORDINATION"  # タスク管理/計画


class EventName(Enum):
    """Standard event names."""

    PLAN_CREATED = "PLAN_CREATED"
    AGENT_SELECTED = "AGENT_SELECTED"
    TOOL_CALLED = "TOOL_CALLED"
    TOOL_RETURNED = "TOOL_RETURNED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RETRY = "RETRY"
    DONE = "DONE"
    ERROR = "ERROR"
    CACHE_HIT = "CACHE_HIT"
    CACHE_MISS = "CACHE_MISS"


@dataclass
class TelemetryEvent:
    """Structured telemetry event.

    Per JARVIS_MASTER.md Section 8, all events must include:
    - run_id, trace_id, step_id (required)
    - event, event_type (required)
    - prompt_hash, tool_input_hash, cache_hit (for reproducibility)

    IMPORTANT: Do NOT put chain-of-thought in payload.
    Only short reason summaries (1-2 lines) are allowed in payload.reason.
    """

    # Required identifiers
    ts: datetime
    level: str  # INFO, WARN, ERROR
    run_id: str
    trace_id: str
    step_id: int

    # Event info
    event: str
    event_type: str  # COGNITIVE, ACTION, COORDINATION

    # Optional context
    task_id: Optional[str] = None
    subtask_id: Optional[str] = None
    agent: Optional[str] = None
    tool: Optional[str] = None

    # Payload (no chain-of-thought!)
    payload: Dict[str, Any] = field(default_factory=dict)

    # Reproducibility fields
    prompt_hash: Optional[str] = None
    tool_input_hash: Optional[str] = None
    cache_hit: Optional[bool] = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        d["ts"] = self.ts.isoformat()
        # Remove None values
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def create(
        cls,
        run_id: str,
        trace_id: str,
        step_id: int,
        event: str,
        event_type: str,
        level: str = "INFO",
        **kwargs,
    ) -> "TelemetryEvent":
        """Factory method for creating events."""
        return cls(
            ts=datetime.now(),
            level=level,
            run_id=run_id,
            trace_id=trace_id,
            step_id=step_id,
            event=event,
            event_type=event_type,
            **kwargs,
        )
