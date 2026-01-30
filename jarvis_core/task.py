"""Task model definitions for Jarvis Core.

The Task object captures the minimal contract shared across planners,
routers, and execution components. It aligns with the specification
in ``docs/JARVIS_MASTER.md`` (Section 5.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    """Canonical Task representation per JARVIS_MASTER.md Section 5.2.

    Attributes:
        task_id: Unique identifier for the task (UUID).
        title: Short descriptive title for the task.
        category: Task category (paper_survey, thesis, job_hunting, generic).
        user_goal: Detailed description of what the user wants to achieve.
        inputs: Additional inputs (query, files, context_notes).
        constraints: Constraints (language, citation_required, etc.).
        priority: Task priority (low, normal, high or numeric 1-3).
        status: Current lifecycle status.
        history: Execution history events.
    """

    task_id: str
    title: str
    category: TaskCategory
    user_goal: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    history: list[Any] = field(default_factory=list)

    # --- Backward compatibility properties ---
    @property
    def id(self) -> str:
        """Alias for task_id (backward compatibility)."""
        return self.task_id

    @property
    def goal(self) -> str:
        """Alias for title (backward compatibility)."""
        return self.title

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
