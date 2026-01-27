import asyncio

import pytest

from jarvis_core.orchestrator.multi_agent import MultiAgentOrchestrator
from jarvis_core.orchestrator.schema import AgentMode, AgentTask


@pytest.mark.integration
def test_multi_agent_parallel_and_conversation():
    async def run_case():
        orchestrator = MultiAgentOrchestrator(max_concurrent_agents=2, default_mode=AgentMode.PLANNING)
        await orchestrator.start()

        task_a = AgentTask(task_id="a", description="Task A", agent_type="unknown")
        task_b = AgentTask(task_id="b", description="Task B", agent_type="unknown")

        agent_a = await orchestrator.spawn_agent(task_a)
        agent_b = await orchestrator.spawn_agent(task_b)

        await orchestrator._queue.join()

        status_a = orchestrator.get_agent_status(agent_a)
        status_b = orchestrator.get_agent_status(agent_b)

        conversation_id = orchestrator.create_conversation("Review", "workspace-1")
        message_id = orchestrator.add_message(conversation_id, agent_a, "agent", "hello")
        inbox = orchestrator.get_inbox()

        await orchestrator.stop()
        return status_a, status_b, message_id, inbox

    status_a, status_b, message_id, inbox = asyncio.run(run_case())

    assert status_a["status"] == "completed"
    assert status_b["status"] == "completed"
    assert message_id is not None
    assert inbox[0]["message_count"] == 1


@pytest.mark.integration
def test_multi_agent_approval_and_callbacks():
    async def run_case():
        orchestrator = MultiAgentOrchestrator(max_concurrent_agents=1, default_mode=AgentMode.PLANNING)
        status_events = []
        approval_events = []

        async def on_status(payload):
            status_events.append(payload)

        async def on_approval(payload):
            approval_events.append(payload)

        orchestrator.register_callback("status_change", on_status)
        orchestrator.register_callback("approval_required", on_approval)

        await orchestrator.start()
        task = AgentTask(task_id="approval", description="Needs approval", agent_type="unknown")
        agent_id = await orchestrator.spawn_agent(task)

        await orchestrator.request_approval(agent_id, "external_call", {"reason": "test"})
        await orchestrator.approve(agent_id, approved=True)

        await orchestrator._queue.join()
        await orchestrator.stop()

        return status_events, approval_events

    status_events, approval_events = asyncio.run(run_case())

    assert any(event["status"] == "waiting_approval" for event in status_events)
    assert approval_events
