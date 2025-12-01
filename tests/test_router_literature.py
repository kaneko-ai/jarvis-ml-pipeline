from pathlib import Path
import sys
import types

# Stub google modules before importing LLM-dependent code to avoid optional dependency errors
google_stub = types.ModuleType("google")
google_genai_stub = types.ModuleType("google.genai")


class _DummyErrors:
    class ServerError(Exception):
        ...

    class ClientError(Exception):
        ...


class _DummyModels:
    @staticmethod
    def generate_content(model: str, contents: str):  # pragma: no cover - stub
        return types.SimpleNamespace(text="")


class _DummyClient:
    def __init__(self, api_key=None):
        self.models = _DummyModels()


google_genai_stub.Client = _DummyClient
google_genai_stub.errors = _DummyErrors
google_stub.genai = google_genai_stub
sys.modules.setdefault("google", google_stub)
sys.modules.setdefault("google.genai", google_genai_stub)

# Ensure project root is on sys.path for direct module imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.agents import AgentResult  # noqa: E402
from jarvis_core.agents.literature import LiteratureSurveyAgent  # noqa: E402
from jarvis_core.registry import AgentRegistry  # noqa: E402
from jarvis_core.router import Router  # noqa: E402
from jarvis_core.task import Task, TaskCategory, TaskPriority, TaskStatus  # noqa: E402


class DummyLLM:
    def chat(self, messages):  # pragma: no cover - simple stub
        return "thought:\n  dummy\nanswer:\n  dummy"


def make_router():
    registry = AgentRegistry.from_file(Path("configs/agents.yaml"))
    return Router(llm=DummyLLM(), registry=registry)


def test_router_uses_literature_agent(monkeypatch):
    def fake_run_task(self, task):  # noqa: ANN001
        return AgentResult(thought="ok", answer="Literature output", meta={"papers": [{"pmid": "1"}]})

    monkeypatch.setattr(LiteratureSurveyAgent, "run_task", fake_run_task)

    router = make_router()
    task = Task(
        id="lit-router",
        category=TaskCategory.LITERATURE_REVIEW,
        goal="Find CD73 papers",
        inputs={"query": "CD73"},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    result = router.run(task)
    assert result.answer == "Literature output"
    assert result.meta["papers"]
