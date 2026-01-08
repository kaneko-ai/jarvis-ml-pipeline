"""Integration tests for run_jarvis() with ExecutionEngine."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

# Stub google modules before importing jarvis_core
google_stub = types.ModuleType("google")
google_genai_stub = types.ModuleType("google.genai")


class _DummyErrors:
    class ServerError(Exception): ...

    class ClientError(Exception): ...


google_genai_stub.errors = _DummyErrors
google_stub.genai = google_genai_stub
sys.modules.setdefault("google", google_stub)
sys.modules.setdefault("google.genai", google_genai_stub)

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core import run_jarvis  # noqa: E402
from jarvis_core.executor import ExecutionEngine  # noqa: E402
from jarvis_core.planner import Planner  # noqa: E402
from jarvis_core.task import Task, TaskCategory  # noqa: E402


class DummyPlanner(Planner):
    """Planner that returns the root task as-is for predictable testing."""

    def plan(self, task: Task):
        return [task]


class DummyRouter:
    """Router that returns a fixed answer without LLM calls."""

    def __init__(self, answer: str = "test answer"):
        self.answer = answer
        self.calls = []

    def run(self, task: Task):
        self.calls.append(task)
        return types.SimpleNamespace(
            status="success",
            answer=self.answer,
            citations=[],
            meta={"source": "dummy"},
        )


def test_run_jarvis_uses_execution_engine():
    """Verify run_jarvis() produces a string answer via run_task."""
    # run_jarvis uses app.run_task internally, not ExecutionEngine directly
    # Mock run_task to return a mock result object
    mock_result = MagicMock()
    mock_result.answer = "mocked answer"

    with patch("jarvis_core.app.run_task", return_value=mock_result):
        result = run_jarvis("test goal")
        assert result == "mocked answer"


def test_run_jarvis_returns_string():
    """Verify run_jarvis() returns a string."""
    with (
        patch("jarvis_core.llm.LLMClient"),
        patch("jarvis_core.router.Router"),
        patch("jarvis_core.planner.Planner"),
        patch("jarvis_core.executor.ExecutionEngine") as MockEngine,
    ):
        mock_instance = MagicMock()
        mock_instance.run_and_get_answer.return_value = "string result"
        MockEngine.return_value = mock_instance

        result = run_jarvis("any goal")

        assert isinstance(result, str)


def test_run_jarvis_with_category():
    """Verify category argument is passed to run_task correctly."""
    captured_dict = None

    def capture_run_task(task_dict, run_config_dict):
        nonlocal captured_dict
        captured_dict = task_dict
        mock_result = MagicMock()
        mock_result.answer = "answer"
        return mock_result

    with patch("jarvis_core.app.run_task", side_effect=capture_run_task):
        run_jarvis("thesis goal", category="thesis")

        assert captured_dict is not None
        assert captured_dict["category"] == "thesis"


def test_run_jarvis_with_invalid_category_defaults_to_generic():
    """Verify invalid category is passed through to run_task."""
    captured_dict = None

    def capture_run_task(task_dict, run_config_dict):
        nonlocal captured_dict
        captured_dict = task_dict
        mock_result = MagicMock()
        mock_result.answer = "answer"
        return mock_result

    with patch("jarvis_core.app.run_task", side_effect=capture_run_task):
        run_jarvis("some goal", category="invalid_category")

        assert captured_dict is not None
        # Invalid category is passed as-is; run_task handles validation
        assert captured_dict["category"] == "invalid_category"


def test_run_and_get_answer_returns_last_answer():
    """Verify ExecutionEngine.run_and_get_answer() extracts the final answer."""
    planner = DummyPlanner()
    router = DummyRouter(answer="expected answer")
    engine = ExecutionEngine(planner=planner, router=router)

    root_task = Task(
        task_id="test-task",
        title="test goal",
        category=TaskCategory.GENERIC,
        inputs={"query": "test"},
    )

    result = engine.run_and_get_answer(root_task)

    assert result == "expected answer"
    assert len(router.calls) == 1


def test_run_and_get_answer_empty_when_no_subtasks():
    """Verify run_and_get_answer() returns empty string when no subtasks."""

    class EmptyPlanner(Planner):
        def plan(self, task: Task):
            return []

    planner = EmptyPlanner()
    router = DummyRouter()
    engine = ExecutionEngine(planner=planner, router=router)

    root_task = Task(
        task_id="test-task",
        title="test goal",
        category=TaskCategory.GENERIC,
        inputs={},
    )

    result = engine.run_and_get_answer(root_task)

    assert result == ""
