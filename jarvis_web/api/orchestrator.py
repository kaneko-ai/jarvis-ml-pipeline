"""Orchestrator API endpoints."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jarvis_core.orchestrator.multi_agent import MultiAgentOrchestrator
from jarvis_core.orchestrator.schema import AgentMode, AgentTask


router = APIRouter(prefix="/api", tags=["orchestrator"])


class SpawnAgentRequest(BaseModel):
    description: str
    agent_type: str
    priority: int = 0
    dependencies: list[str] = []
    mode: str | None = None
    conversation_id: str | None = None


class ApprovalRequest(BaseModel):
    approved: bool


_orchestrator: MultiAgentOrchestrator | None = None


def _get_orchestrator() -> MultiAgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator(max_concurrent_agents=3, default_mode=AgentMode.PLANNING)
    return _orchestrator


async def _ensure_started() -> MultiAgentOrchestrator:
    orchestrator = _get_orchestrator()
    await orchestrator.start()
    return orchestrator


@router.post("/agents/spawn")
async def spawn_agent(payload: SpawnAgentRequest) -> dict[str, Any]:
    orchestrator = await _ensure_started()
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        description=payload.description,
        agent_type=payload.agent_type,
        priority=payload.priority,
        dependencies=payload.dependencies,
    )
    mode = AgentMode(payload.mode) if payload.mode else None
    agent_id = await orchestrator.spawn_agent(task, mode=mode, conversation_id=payload.conversation_id)
    return {"agent_id": agent_id}


@router.get("/agents")
async def list_agents() -> dict[str, Any]:
    orchestrator = _get_orchestrator()
    return {"agents": orchestrator.get_all_agents()}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> dict[str, Any]:
    orchestrator = _get_orchestrator()
    status = orchestrator.get_agent_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail="agent_not_found")
    return {"agent": status}


@router.post("/agents/{agent_id}/approve")
async def approve_agent(agent_id: str, payload: ApprovalRequest) -> dict[str, Any]:
    orchestrator = _get_orchestrator()
    await orchestrator.approve(agent_id, approved=payload.approved)
    status = orchestrator.get_agent_status(agent_id)
    return {"agent": status}


@router.post("/agents/{agent_id}/cancel")
async def cancel_agent(agent_id: str) -> dict[str, Any]:
    orchestrator = _get_orchestrator()
    await orchestrator.approve(agent_id, approved=False)
    status = orchestrator.get_agent_status(agent_id)
    return {"agent": status}
