from jarvis_core.registry import AgentRegistry  # noqa: E402
from jarvis_core.router import Router  # noqa: E402
from jarvis_core.task import Task, TaskCategory, TaskPriority, TaskStatus  # noqa: E402
import sys
import types
from pathlib import Path

# Stub google modules before importing LLM-dependent code to avoid optional dependency errors
google_stub = types.ModuleType("google")
google_genai_stub = types.ModuleType("google.genai")


class _DummyErrors:
    class ServerError(Exception): ...

    class ClientError(Exception): ...


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
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class DummyLLM:
    def chat(self, messages):  # pragma: no cover - simple stub
        return "dummy answer"


def make_router():
    registry = AgentRegistry.from_file(Path("configs/agents.yaml"))
    return Router(llm=DummyLLM(), registry=registry)


def test_router_selects_agent_by_category():
    router = make_router()
    task = Task(
        task_id="t1",
        title="Find CD73 papers",
        category=TaskCategory.PAPER_SURVEY,
        inputs={"query": "CD73", "context": "thesis background"},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    result = router.run(task)
    assert "fetching papers" in result.answer
    assert result.meta and result.meta.get("source") == "paper_fetcher_stub"


def test_router_respects_agent_hint():
    router = make_router()
    task = Task(
        task_id="t2",
        title="Analyze PDF",
        category=TaskCategory.PAPER_SURVEY,
        inputs={"agent_hint": "mygpt_paper_analyzer", "context": "analysis"},
        constraints={},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
    )

    result = router.run(task)
    assert "analyzing papers" in result.answer
    assert result.meta and result.meta.get("source") == "mygpt_paper_analyzer_stub"