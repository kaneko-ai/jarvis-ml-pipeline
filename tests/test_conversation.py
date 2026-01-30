from jarvis_core.orchestrator.multi_agent import MultiAgentOrchestrator
from jarvis_core.orchestrator.schema import AgentMode


def test_conversation_management_flow():
    orchestrator = MultiAgentOrchestrator(max_concurrent_agents=1, default_mode=AgentMode.PLANNING)
    conversation_id = orchestrator.create_conversation(
        title="Literature Review",
        workspace="/tmp/workspace",
    )
    message_id = orchestrator.add_message(
        conversation_id=conversation_id,
        agent_id="agent-1",
        role="user",
        content="Please summarize recent work.",
        artifacts=["note.md"],
    )

    conversation = orchestrator.get_conversation(conversation_id)
    assert conversation is not None
    assert conversation.messages[0].message_id == message_id
    assert conversation.messages[0].content == "Please summarize recent work."

    inbox = orchestrator.get_inbox()
    assert inbox[0]["conversation_id"] == conversation_id
    assert inbox[0]["message_count"] == 1
