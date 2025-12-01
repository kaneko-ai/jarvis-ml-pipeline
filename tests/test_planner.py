from jarvis_core.planner import Planner
from jarvis_core.task import Task, TaskCategory, TaskPriority, TaskStatus


def test_planner_generates_subtasks_for_supported_category():
    planner = Planner()
    task = Task(
        id="root",
        category=TaskCategory.PAPER_SURVEY,
        goal="Map CD73 literature",
        inputs={"query": "CD73", "context": "background"},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    subtasks = planner.plan(task)

    assert len(subtasks) == 3
    assert all(sub.id.startswith("root:") for sub in subtasks)
    assert all(sub.category == task.category for sub in subtasks)
    assert all(task.goal.split(" — ")[0] in sub.goal for sub in subtasks)


def test_planner_falls_back_for_unknown_category():
    planner = Planner()
    task = Task(
        id="generic",
        category=TaskCategory.GENERIC,
        goal="General help",
        inputs={},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    subtasks = planner.plan(task)

    assert len(subtasks) == 1
    assert subtasks[0] is task
