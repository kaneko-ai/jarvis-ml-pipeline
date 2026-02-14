"""Schemas for multi-agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AgentStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentMode(str, Enum):
    PLANNING = "planning"
    FAST = "fast"


@dataclass
class AgentTask:
    task_id: str
    description: str
    agent_type: str
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AgentInstance:
    agent_id: str
    task: AgentTask
    status: AgentStatus = AgentStatus.IDLE
    mode: AgentMode = AgentMode.PLANNING
    progress: float = 0.0
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
