"""Multi-agent orchestrator with approval flow support."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class AgentStatus(str, Enum):
    """Status values for agents and tasks."""

    IDLE = "idle"
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Task assigned to an agent."""

    id: str
    agent_id: str
    description: str
    payload: dict[str, Any]
    status: AgentStatus = AgentStatus.PENDING
    result: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentState:
    """Runtime state for a registered agent."""

    id: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    current_task_id: str | None = None
    last_error: str | None = None
    approval_request: dict[str, Any] | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationMessage:
    """Message within a conversation."""

    id: str
    agent_id: str
    role: str
    content: str
    artifacts: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Conversation:
    """Conversation container."""

    id: str
    title: str
    workspace: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    messages: list[ConversationMessage] = field(default_factory=list)


from jarvis_core.orchestrator.artifact_store import ArtifactStore


class MultiAgentOrchestrator:
    """Orchestrate multi-agent execution and approvals."""

    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}
        self._agent_states: dict[str, AgentState] = {}
        self._tasks: dict[str, AgentTask] = {}
        self._task_queue: asyncio.Queue[AgentTask] = asyncio.Queue()
        self.artifact_store = ArtifactStore()
        self._conversations: dict[str, Conversation] = {}
        self._callbacks: dict[str, list[Callable[..., Coroutine[Any, Any, None]]]] = {
            "status_change": [],
            "artifact_created": [],
            "approval_required": [],
            "progress_update": [],
        }
        self.on_approval_required: Callable[[str, dict[str, Any]], Any] | None = None

    def register_agent(self, agent: Any) -> None:
        """Register an agent instance."""
        agent_id = agent.agent_id
        self._agents[agent_id] = agent
        self._agent_states[agent_id] = AgentState(id=agent_id, agent_type=agent.agent_type)

    def create_task(self, agent_id: str, description: str, payload: dict[str, Any]) -> str:
        """Create and enqueue a task for an agent."""
        task_id = f"task_{uuid4().hex}"
        task = AgentTask(
            id=task_id,
            agent_id=agent_id,
            description=description,
            payload=payload,
        )
        self._tasks[task_id] = task
        self._task_queue.put_nowait(task)
        return task_id

    def create_conversation(self, title: str, workspace: str) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = f"conv_{uuid4().hex}"
        conversation = Conversation(id=conversation_id, title=title, workspace=workspace)
        self._conversations[conversation_id] = conversation
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        agent_id: str,
        role: str,
        content: str,
        artifacts: list[str] | None = None,
    ) -> str:
        """Add a message to a conversation."""
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
        message_id = f"msg_{uuid4().hex}"
        message = ConversationMessage(
            id=message_id,
            agent_id=agent_id,
            role=role,
            content=content,
            artifacts=artifacts or [],
        )
        conversation.messages.append(message)
        conversation.updated_at = datetime.utcnow()
        return message_id

    def get_inbox(self) -> list[dict]:
        """Return conversations sorted by updated time."""
        conversations = sorted(
            self._conversations.values(),
            key=lambda conv: conv.updated_at,
            reverse=True,
        )
        return [
            {
                "id": conv.id,
                "title": conv.title,
                "workspace": conv.workspace,
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages),
            }
            for conv in conversations
        ]

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)

    async def spawn_agent(self, agent_type: str, description: str, payload: dict[str, Any]) -> AgentTask:
        """Spawn an agent task by agent type."""
        agent = self._find_agent_by_type(agent_type)
        if agent is None:
            raise ValueError(f"Unknown agent type: {agent_type}")
        task_id = self.create_task(agent.agent_id, description, payload)
        state = self._agent_states[agent.agent_id]
        state.current_task_id = task_id
        state.status = AgentStatus.PENDING
        state.updated_at = datetime.utcnow()
        task = self._tasks[task_id]
        await self._emit_event(
            "status_change",
            {"agent_id": agent.agent_id, "status": state.status.value},
        )
        return task

    def get_agent_status(self, agent_id: str) -> dict | None:
        """Return agent status by ID."""
        state = self._agent_states.get(agent_id)
        if not state:
            return None
        return {
            "agent_id": state.id,
            "agent_type": state.agent_type,
            "status": state.status.value,
            "current_task_id": state.current_task_id,
            "updated_at": state.updated_at.isoformat(),
        }

    def get_all_agents(self) -> list[dict]:
        """Return all agent statuses."""
        return [
            {
                "agent_id": state.id,
                "agent_type": state.agent_type,
                "status": state.status.value,
                "current_task_id": state.current_task_id,
                "updated_at": state.updated_at.isoformat(),
            }
            for state in self._agent_states.values()
        ]

    async def cancel_agent(self, agent_id: str) -> None:
        """Cancel an agent task."""
        state = self._agent_states.get(agent_id)
        if not state:
            raise ValueError(f"Unknown agent: {agent_id}")
        state.status = AgentStatus.CANCELLED
        state.updated_at = datetime.utcnow()
        if state.current_task_id and state.current_task_id in self._tasks:
            self._tasks[state.current_task_id].status = AgentStatus.CANCELLED
        await self._emit_event(
            "status_change",
            {"agent_id": agent_id, "status": state.status.value},
        )

    def register_callback(
        self, event_type: str, callback: Callable[..., Coroutine[Any, Any, None]]
    ) -> Callable[[], None]:
        """Register an async callback for agent events."""
        if event_type not in self._callbacks:
            raise ValueError(f"Unsupported event type: {event_type}")
        self._callbacks[event_type].append(callback)
        return lambda: self._callbacks[event_type].remove(callback)

    async def _emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        callbacks = list(self._callbacks.get(event_type, []))
        for callback in callbacks:
            await callback(payload)

    async def notify_artifact_created(self, agent_id: str, artifact_path: str) -> None:
        """Emit an artifact_created event."""
        await self._emit_event(
            "artifact_created",
            {"agent_id": agent_id, "artifact_path": artifact_path},
        )

    async def notify_progress_update(self, agent_id: str, progress: dict[str, Any]) -> None:
        """Emit a progress_update event."""
        await self._emit_event(
            "progress_update",
            {"agent_id": agent_id, "progress": progress},
        )

    async def request_approval(self, agent_id: str, approval_type: str, details: dict) -> None:
        """Request approval for an agent's next action."""
        state = self._agent_states.get(agent_id)
        if state is None:
            raise ValueError(f"Unknown agent: {agent_id}")
        state.status = AgentStatus.WAITING_APPROVAL
        state.approval_request = {"type": approval_type, "details": details}
        state.updated_at = datetime.utcnow()
        if self.on_approval_required is not None:
            await asyncio.to_thread(self.on_approval_required, agent_id, state.approval_request)
        await self._emit_event(
            "approval_required",
            {
                "agent_id": agent_id,
                "approval_type": approval_type,
                "details": details,
            },
        )
        await self._emit_event(
            "status_change",
            {"agent_id": agent_id, "status": state.status.value},
        )

    async def approve(self, agent_id: str, approved: bool) -> None:
        """Approve or reject an agent waiting for approval."""
        state = self._agent_states.get(agent_id)
        if state is None:
            raise ValueError(f"Unknown agent: {agent_id}")
        if approved:
            state.status = AgentStatus.PENDING
            state.updated_at = datetime.utcnow()
            state.approval_request = None
            task_id = state.current_task_id
            if task_id and task_id in self._tasks:
                task = self._tasks[task_id]
                if task.status == AgentStatus.WAITING_APPROVAL:
                    task.status = AgentStatus.PENDING
                self._task_queue.put_nowait(task)
        else:
            state.status = AgentStatus.CANCELLED
            state.updated_at = datetime.utcnow()
            task_id = state.current_task_id
            if task_id and task_id in self._tasks:
                self._tasks[task_id].status = AgentStatus.CANCELLED
        await self._emit_event(
            "status_change",
            {"agent_id": agent_id, "status": state.status.value, "approved": approved},
        )

    def _find_agent_by_type(self, agent_type: str) -> Any | None:
        for agent in self._agents.values():
            if agent.agent_type == agent_type:
                return agent
        return None
