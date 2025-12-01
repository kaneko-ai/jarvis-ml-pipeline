import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path for direct module imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.task import (  # noqa: E402
    Task,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)


def test_task_creation_with_defaults():
    task = Task(
        id="task-1",
        category=TaskCategory.PAPER_SURVEY,
        goal="Survey CD73 literature",
        inputs={"query": "CD73", "files": []},
    )

    assert task.priority == TaskPriority.NORMAL
    assert task.status == TaskStatus.PENDING
    assert task.history == []
    assert task.category is TaskCategory.PAPER_SURVEY
    assert task.inputs["query"] == "CD73"


def test_task_rejects_invalid_category():
    with pytest.raises(ValueError):
        Task(
            id="task-2",
            category="invalid",  # type: ignore[arg-type]
            goal="Do something",
            inputs={},
        )


def test_task_rejects_invalid_priority_and_status():
    with pytest.raises(ValueError):
        Task(
            id="task-3",
            category=TaskCategory.GENERIC,
            goal="Generic goal",
            inputs={},
            priority="urgent",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError):
        Task(
            id="task-4",
            category=TaskCategory.GENERIC,
            goal="Generic goal",
            inputs={},
            status="unknown",  # type: ignore[arg-type]
        )


def test_history_default_is_isolated():
    first = Task(id="t1", category=TaskCategory.STUDY, goal="Study", inputs={})
    second = Task(id="t2", category=TaskCategory.STUDY, goal="Study", inputs={})

    first.history.append("step")
    assert first.history == ["step"]
    assert second.history == []
