import asyncio

import pytest

from jarvis_core.orchestrator.multi_agent import MultiAgentOrchestrator
from jarvis_core.orchestrator.schema import AgentMode, AgentTask


@pytest.mark.asyncio
async def test_orchestrator_executes_agent():
    orchestrator = MultiAgentOrchestrator(max_concurrent_agents=1, default_mode=AgentMode.PLANNING)
    await orchestrator.start()
    task = AgentTask(task_id="task-1", description="Test task", agent_type="test")
    agent_id = await orchestrator.spawn_agent(task, mode=None, conversation_id=None)

    status = None
    for _ in range(10):
        status = orchestrator.get_agent_status(agent_id)
        if status and status.get("status") == "completed":
            break
        await asyncio.sleep(0.01)

    await orchestrator.stop()

    assert status is not None
    assert status["status"] == "completed"


def test_orchestrator_lists_agents():
    orchestrator = MultiAgentOrchestrator(max_concurrent_agents=1, default_mode=AgentMode.PLANNING)
    task = AgentTask(task_id="task-2", description="List test", agent_type="test")
    agent_id = asyncio.run(orchestrator.spawn_agent(task, mode=None, conversation_id=None))
    agents = orchestrator.get_all_agents()
    assert any(agent["agent_id"] == agent_id for agent in agents)