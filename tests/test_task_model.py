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
        task_id="task-1",
        title="Survey CD73 literature",
        category=TaskCategory.PAPER_SURVEY,
        inputs={"query": "CD73", "files": []},
    )

    assert task.priority == TaskPriority.NORMAL
    assert task.status == TaskStatus.PENDING
    assert task.history == []
    assert task.category is TaskCategory.PAPER_SURVEY
    assert task.inputs["query"] == "CD73"
    # Backward compatibility
    assert task.id == "task-1"
    assert task.goal == "Survey CD73 literature"


def test_task_rejects_invalid_category():
    with pytest.raises(ValueError):
        Task(
            task_id="task-2",
            title="Do something",
            category="invalid",  # type: ignore[arg-type]
        )


def test_task_rejects_invalid_priority_and_status():
    with pytest.raises(ValueError):
        Task(
            task_id="task-3",
            title="Generic goal",
            category=TaskCategory.GENERIC,
            priority="urgent",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError):
        Task(
            task_id="task-4",
            title="Generic goal",
            category=TaskCategory.GENERIC,
            status="unknown",  # type: ignore[arg-type]
        )


def test_history_default_is_isolated():
    first = Task(task_id="t1", title="Study", category=TaskCategory.STUDY)
    second = Task(task_id="t2", title="Study", category=TaskCategory.STUDY)

    first.history.append("step")
    assert first.history == ["step"]
    assert second.history == []


def test_task_schema_compliance():
    """Verify Task fields match JARVIS_MASTER.md Section 5.2."""
    task = Task(
        task_id="uuid-123",
        title="CD73に関する最新論文サーベイ",
        category=TaskCategory.PAPER_SURVEY,
        user_goal="CD73に関する最新論文を調べ、要点を整理してまとめてほしい",
        inputs={"query": "CD73", "files": [], "context_notes": ""},
        constraints={"language": "ja", "citation_required": True},
    )

    # Verify spec-required fields exist and have correct values
    assert task.task_id == "uuid-123"
    assert task.title == "CD73に関する最新論文サーベイ"
    assert task.category == TaskCategory.PAPER_SURVEY
    assert task.user_goal == "CD73に関する最新論文を調べ、要点を整理してまとめてほしい"
    assert task.inputs["query"] == "CD73"
    assert task.constraints["language"] == "ja"

