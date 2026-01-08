import sys
import types
from pathlib import Path

# Stub google modules before importing executor/router to avoid optional dependency errors
google_stub = types.ModuleType("google")
google_genai_stub = types.ModuleType("google.genai")


class _DummyErrors:
    class ServerError(Exception):
        ...

    class ClientError(Exception):
        ...


google_genai_stub.errors = _DummyErrors
google_stub.genai = google_genai_stub
sys.modules.setdefault("google", google_stub)
sys.modules.setdefault("google.genai", google_genai_stub)

# Ensure project root is on sys.path for direct module imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.executor import ExecutionEngine  # noqa: E402
from jarvis_core.planner import Planner  # noqa: E402
from jarvis_core.task import Task, TaskCategory, TaskPriority, TaskStatus  # noqa: E402


class DummyPlanner(Planner):
    def __init__(self, subtasks):
        super().__init__()
        self.subtasks = subtasks
        self.called = False

    def plan(self, task: Task):
        self.called = True
        return self.subtasks


class DummyRouter:
    def __init__(self):
        self.calls = []

    def run(self, task: Task):
        self.calls.append(task.goal)
        return types.SimpleNamespace(answer=f"done: {task.goal}", meta={"task": task.id})


def make_subtasks():
    return [
        Task(
            task_id="root:1",
            title="Step 1",
            category=TaskCategory.JOB_HUNTING,
            inputs={},
            constraints={},
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
        ),
        Task(
            task_id="root:2",
            title="Step 2",
            category=TaskCategory.JOB_HUNTING,
            inputs={},
            constraints={},
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
        ),
    ]


def test_execution_engine_runs_subtasks_and_updates_status():
    subtasks = make_subtasks()
    planner = DummyPlanner(subtasks)
    router = DummyRouter()
    engine = ExecutionEngine(planner=planner, router=router)

    root_task = Task(
        task_id="root",
        title="Prepare materials",
        category=TaskCategory.JOB_HUNTING,
        inputs={},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    executed = engine.run(root_task)

    assert planner.called
    assert router.calls == ["Step 1", "Step 2"]
    assert len(executed) == 2
    assert all(task.status == TaskStatus.DONE for task in executed)
    assert all(any(event.get("event") == "complete" for event in task.history) for task in executed)
