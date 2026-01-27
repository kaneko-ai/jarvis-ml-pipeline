"""Core multi-agent orchestrator implementation."""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .conversation import Conversation, ConversationMessage
from .schema import AgentInstance, AgentMode, AgentStatus, AgentTask


class MultiAgentOrchestrator:
    """Manage multiple agents concurrently with a task queue."""

    def __init__(self, max_concurrent_agents: int, default_mode: AgentMode) -> None:
        self.max_concurrent_agents = max_concurrent_agents
        self.default_mode = default_mode
        self._queue: asyncio.Queue[tuple[str, AgentTask, AgentMode, str | None]] = asyncio.Queue()
        self._agents: dict[str, AgentInstance] = {}
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._conversations: dict[str, Conversation] = {}

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
        if conversation_id and conversation_id in self._conversations:
            conversation = self._conversations[conversation_id]
            if agent_id not in conversation.agents:
                conversation.agents.append(agent_id)
                conversation.updated_at = datetime.utcnow()
        await self._queue.put((agent_id, task, instance.mode, conversation_id))
        return agent_id

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

    def _serialize_agent(self, instance: AgentInstance) -> dict[str, Any]:
        data = asdict(instance)
        data["status"] = instance.status.value
        data["mode"] = instance.mode.value
        data["started_at"] = instance.started_at.isoformat() if instance.started_at else None
        data["completed_at"] = (
            instance.completed_at.isoformat() if instance.completed_at else None
        )
        data["task"]["created_at"] = instance.task.created_at.isoformat()
        return data

    async def _worker(self) -> None:
        while self._running:
            agent_id, task, mode, conversation_id = await self._queue.get()
            instance = self._agents.get(agent_id)
            if not instance:
                self._queue.task_done()
                continue
            instance.status = AgentStatus.EXECUTING
            instance.started_at = datetime.utcnow()
            try:
                await asyncio.sleep(0)
                instance.progress = 1.0
                instance.status = AgentStatus.COMPLETED
                instance.completed_at = datetime.utcnow()
            except Exception as exc:  # pragma: no cover - defensive
                instance.status = AgentStatus.FAILED
                instance.errors.append(str(exc))
                instance.completed_at = datetime.utcnow()
            finally:
                self._queue.task_done()
