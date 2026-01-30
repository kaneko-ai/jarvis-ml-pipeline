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


def test_registry_loads_agents_from_yaml():
    registry = AgentRegistry.from_file(Path("configs/agents.yaml"))

    default = registry.get_default_agent_for_category("paper_survey")
    assert default is not None
    assert default.name == "paper_fetcher"

    job_agents = {agent.name for agent in registry.get_agents_for_category("job_hunting")}
    assert "job_assistant" in job_agents
    assert "es_edit" in job_agents


def test_registry_instantiates_agent_stub():
    registry = AgentRegistry.from_file(Path("configs/agents.yaml"))
    agent = registry.create_agent_instance("paper_fetcher")

    result = agent.run_single(DummyLLM(), "test paper fetch")
    assert "fetching papers" in result.answer
    assert result.meta and result.meta.get("source") == "paper_fetcher_stub"

    with pytest.raises(KeyError):
        registry.create_agent_instance("unknown_agent")