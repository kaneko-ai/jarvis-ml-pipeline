from jarvis_core.registry import AgentRegistry  # noqa: E402
from pathlib import Path

import pytest

# Ensure project root is on sys.path for direct module imports
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class DummyLLM:
    def chat(self, messages):  # pragma: no cover - simple stub
        return "dummy answer"


class _FakePubMedClient:
    def search_and_fetch(self, query: str, max_results: int = 5):
        from jarvis_core.sources.pubmed_client import PubMedArticle

        return [
            PubMedArticle(
                pmid=str(1000 + i),
                title=f"{query} study {i + 1}",
                abstract=f"Abstract for {query} study {i + 1}",
                authors=["Tester A"],
                journal="Test Journal",
                pub_date="2026",
            )
            for i in range(max_results)
        ]


class _EmptySourceClient:
    def search(self, *args, **kwargs):  # pragma: no cover - simple stub
        return []


def test_registry_loads_agents_from_yaml():
    registry = AgentRegistry.from_file(Path("configs/agents.yaml"))

    default = registry.get_default_agent_for_category("paper_survey")
    assert default is not None
    assert default.name == "paper_fetcher"

    job_agents = {agent.name for agent in registry.get_agents_for_category("job_hunting")}
    assert "job_assistant" in job_agents
    assert "es_edit" in job_agents


def test_registry_instantiates_paper_fetcher(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("jarvis_core.agents.PubMedClient", _FakePubMedClient)
    monkeypatch.setattr("jarvis_core.agents.ArxivClient", _EmptySourceClient)
    monkeypatch.setattr("jarvis_core.agents.CrossrefClient", _EmptySourceClient)

    registry = AgentRegistry.from_file(Path("configs/agents.yaml"))
    agent = registry.create_agent_instance("paper_fetcher")

    result = agent.run_single(DummyLLM(), "test paper fetch")
    assert "Found 5 papers" in result.answer
    assert result.meta and result.meta.get("source") == "paper_fetcher"
    assert len(result.meta.get("papers", [])) == 5

    with pytest.raises(KeyError):
        registry.create_agent_instance("unknown_agent")
