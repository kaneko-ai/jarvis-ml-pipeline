"""Task model definitions for Jarvis Core.

The Task object captures the minimal contract shared across planners,
routers, and execution components. It aligns with the abstract
specification in ``docs/jarvis_vision.md`` and keeps validation light
while enforcing allowed enum values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class TaskCategory(str, Enum):
    """Supported task categories for Jarvis Core."""

    PAPER_SURVEY = "paper_survey"
    THESIS = "thesis"
    STUDY = "study"
    JOB_HUNTING = "job_hunting"
    GENERIC = "generic"


class TaskPriority(str, Enum):
    """Relative priority of a task."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Lifecycle state of a task."""

    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    """Canonical Task representation used by Jarvis Core components."""

    id: str
    category: TaskCategory
    goal: str
    inputs: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    history: List[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.category = self._validate_enum(self.category, TaskCategory, "category")
        self.priority = self._validate_enum(self.priority, TaskPriority, "priority")
        self.status = self._validate_enum(self.status, TaskStatus, "status")
        self._validate_mapping("inputs", self.inputs)
        self._validate_mapping("constraints", self.constraints)
        if self.history is None:
            self.history = []

    @staticmethod
    def _validate_enum(value: Any, enum_cls: type[Enum], field_name: str) -> Enum:
        if isinstance(value, enum_cls):
            return value
        try:
            return enum_cls(value)
        except ValueError as exc:  # pragma: no cover - explicit mapping to ValueError
            raise ValueError(f"Invalid {field_name}: {value}") from exc

    @staticmethod
    def _validate_mapping(field_name: str, value: Any) -> None:
        if not isinstance(value, dict):
            raise TypeError(f"{field_name} must be a dictionary; got {type(value).__name__}")
