"""Core multi-agent orchestrator implementation."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Awaitable, Callable

from .conversation import Conversation, ConversationMessage
from .schema import AgentInstance, AgentMode, AgentStatus, AgentTask


class MultiAgentOrchestrator:
    """Manage multiple agents concurrently with a task queue."""

    def __init__(self, max_concurrent_agents: int, default_mode: AgentMode) -> None:
        self.max_concurrent_agents = max_concurrent_agents
        self.default_mode = default_mode
        self._queue: asyncio.Queue[tuple[str, AgentTask, AgentMode, str | None]] = asyncio.Queue()
        self._agents: dict[str, AgentInstance] = {}
        self._agent_conversations: dict[str, str | None] = {}
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._conversations: dict[str, Conversation] = {}
        self._pending_approvals: dict[str, dict[str, Any]] = {}
        self.on_approval_required: Callable[[dict[str, Any]], Awaitable[None]] | None = None
        self._callbacks: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = {
            "status_change": [],
            "artifact_created": [],
            "approval_required": [],
            "progress_update": [],
        }

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for _ in range(self.max_concurrent_agents):
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        self._running = False
        for worker in self._workers:
            worker.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def spawn_agent(
        self,
        task: AgentTask,
        mode: AgentMode | None = None,
        conversation_id: str | None = None,
    ) -> str:
        agent_id = str(uuid.uuid4())
        instance = AgentInstance(
            agent_id=agent_id,
            task=task,
            status=AgentStatus.PLANNING,
            mode=mode or self.default_mode,
            started_at=None,
            completed_at=None,
        )
        self._agents[agent_id] = instance
        self._agent_conversations[agent_id] = conversation_id
        if conversation_id and conversation_id in self._conversations:
            conversation = self._conversations[conversation_id]
            if agent_id not in conversation.agents:
                conversation.agents.append(agent_id)
                conversation.updated_at = datetime.utcnow()
        await self._queue.put((agent_id, task, instance.mode, conversation_id))
        return agent_id

    def register_callback(
        self, event_type: str, callback: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        if event_type not in self._callbacks:
            raise ValueError(f"Unsupported event type: {event_type}")
        self._callbacks[event_type].append(callback)

    async def request_approval(self, agent_id: str, approval_type: str, details: dict) -> None:
        instance = self._agents.get(agent_id)
        if not instance:
            return
        await self._set_status(instance, AgentStatus.WAITING_APPROVAL)
        self._pending_approvals[agent_id] = {
            "approval_type": approval_type,
            "details": details,
            "task": instance.task,
            "mode": instance.mode,
            "conversation_id": self._agent_conversations.get(agent_id),
        }
        payload = {
            "agent_id": agent_id,
            "approval_type": approval_type,
            "details": details,
        }
        if self.on_approval_required:
            await self.on_approval_required(payload)
        await self._emit_event("approval_required", payload)

    async def approve(self, agent_id: str, approved: bool) -> None:
        instance = self._agents.get(agent_id)
        if not instance:
            return
        if not approved:
            await self._set_status(instance, AgentStatus.CANCELLED)
            self._pending_approvals.pop(agent_id, None)
            return
        pending = self._pending_approvals.pop(agent_id, None)
        if not pending:
            return
        await self._set_status(instance, AgentStatus.PLANNING)
        await self._queue.put(
            (agent_id, pending["task"], pending["mode"], pending["conversation_id"])
        )

    def create_conversation(self, title: str, workspace: str) -> str:
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = Conversation(
            conversation_id=conversation_id,
            title=title,
            workspace=workspace,
        )
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        agent_id: str,
        role: str,
        content: str,
        artifacts: list[str] | None = None,
    ) -> str:
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            raise KeyError(f"Conversation not found: {conversation_id}")
        message_id = str(uuid.uuid4())
        message = ConversationMessage(
            message_id=message_id,
            agent_id=agent_id,
            role=role,
            content=content,
            artifacts=artifacts or [],
        )
        conversation.messages.append(message)
        if agent_id not in conversation.agents:
            conversation.agents.append(agent_id)
        conversation.updated_at = datetime.utcnow()
        return message_id

    def get_inbox(self) -> list[dict]:
        conversations = sorted(
            self._conversations.values(),
            key=lambda item: item.updated_at,
            reverse=True,
        )
        inbox = []
        for conversation in conversations:
            inbox.append(
                {
                    "conversation_id": conversation.conversation_id,
                    "title": conversation.title,
                    "workspace": conversation.workspace,
                    "status": conversation.status,
                    "updated_at": conversation.updated_at.isoformat(),
                    "created_at": conversation.created_at.isoformat(),
                    "message_count": len(conversation.messages),
                    "agents": list(conversation.agents),
                }
            )
        return inbox

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)

    def get_agent_status(self, agent_id: str) -> dict | None:
        instance = self._agents.get(agent_id)
        if not instance:
            return None
        return self._serialize_agent(instance)

    def get_all_agents(self) -> list[dict]:
        return [self._serialize_agent(instance) for instance in self._agents.values()]

    def find_agent_id(self, task_id: str) -> str | None:
        for agent_id, instance in self._agents.items():
            if instance.task.task_id == task_id:
                return agent_id
        return None

    async def record_artifact(self, agent_id: str, artifact_path: str) -> None:
        instance = self._agents.get(agent_id)
        if not instance:
            return
        instance.artifacts.append(artifact_path)
        await self._emit_event(
            "artifact_created",
            {"agent_id": agent_id, "artifact_path": artifact_path},
        )

    async def update_progress(self, agent_id: str, progress: float) -> None:
        instance = self._agents.get(agent_id)
        if not instance:
            return
        instance.progress = progress
        await self._emit_event(
            "progress_update",
            {"agent_id": agent_id, "progress": progress},
        )

    def _serialize_agent(self, instance: AgentInstance) -> dict[str, Any]:
        data = asdict(instance)
        data["status"] = instance.status.value
        data["mode"] = instance.mode.value
        data["started_at"] = instance.started_at.isoformat() if instance.started_at else None
        data["completed_at"] = instance.completed_at.isoformat() if instance.completed_at else None
        data["task"]["created_at"] = instance.task.created_at.isoformat()
        return data

    async def _worker(self) -> None:
        while self._running:
            agent_id, task, mode, conversation_id = await self._queue.get()
            instance = self._agents.get(agent_id)
            if not instance:
                self._queue.task_done()
                continue
            await self._set_status(instance, AgentStatus.EXECUTING)
            instance.started_at = datetime.utcnow()
            try:
                handler = self._resolve_agent(task.agent_type)
                if handler:
                    await handler.execute(task, self)
                else:
                    await asyncio.sleep(0)
                await self.update_progress(agent_id, 1.0)
                await self._set_status(instance, AgentStatus.COMPLETED)
                instance.completed_at = datetime.utcnow()
            except Exception as exc:  # pragma: no cover - defensive
                await self._set_status(instance, AgentStatus.FAILED)
                instance.errors.append(str(exc))
                instance.completed_at = datetime.utcnow()
            finally:
                self._queue.task_done()

    async def _set_status(self, instance: AgentInstance, status: AgentStatus) -> None:
        if instance.status == status:
            return
        instance.status = status
        await self._emit_event(
            "status_change",
            {"agent_id": instance.agent_id, "status": status.value},
        )

    async def _emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        for callback in self._callbacks.get(event_type, []):
            await callback(payload)

    def _resolve_agent(self, agent_type: str):
        if agent_type == "research":
            from .agents.research import ResearchAgent

            return ResearchAgent()
        if agent_type == "browser":
            from .agents.browser import BrowserAgent

            return BrowserAgent()
        return None
