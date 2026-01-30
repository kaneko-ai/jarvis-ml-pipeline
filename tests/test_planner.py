from jarvis_core.planner import Planner
from jarvis_core.task import Task, TaskCategory, TaskPriority, TaskStatus


def test_planner_generates_subtasks_for_supported_category():
    planner = Planner()
    task = Task(
        task_id="root",
        title="Map CD73 literature",
        category=TaskCategory.PAPER_SURVEY,
        user_goal="Map CD73 literature",
        inputs={"query": "CD73", "context": "background"},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    subtasks = planner.plan(task)

    assert len(subtasks) == 3
    assert all(sub.task_id.startswith("root:") for sub in subtasks)
    assert all(sub.category == task.category for sub in subtasks)
    assert all(task.title.split(" — ")[0] in sub.title for sub in subtasks)


def test_planner_falls_back_for_unknown_category():
    planner = Planner()
    task = Task(
        task_id="generic",
        title="General help",
        category=TaskCategory.GENERIC,
        inputs={},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    subtasks = planner.plan(task)

    assert len(subtasks) == 1
    assert subtasks[0] is task