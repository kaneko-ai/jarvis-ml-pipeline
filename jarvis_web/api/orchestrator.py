"""Orchestrator API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jarvis_web.api.state import get_orchestrator


router = APIRouter()


class SpawnRequest(BaseModel):
    """Request to spawn an agent."""

    agent_type: str = Field(..., description="Type of agent to spawn.")
    description: str = Field(..., description="Task description.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Task payload.")


class ApprovalRequest(BaseModel):
    """Request to approve or reject an agent."""

    approved: bool = Field(..., description="Whether the action is approved.")


@router.post("/api/agents/spawn")
async def spawn_agent(request: SpawnRequest) -> dict[str, Any]:
    orchestrator = get_orchestrator()
    try:
        task = await orchestrator.spawn_agent(
            request.agent_type,
            request.description,
            request.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "agent_id": task.agent_id,
        "task_id": task.id,
        "status": task.status.value,
    }


@router.get("/api/agents")
async def list_agents() -> list[dict[str, Any]]:
    orchestrator = get_orchestrator()
    return orchestrator.get_all_agents()


@router.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str) -> dict[str, Any]:
    orchestrator = get_orchestrator()
    status = orchestrator.get_agent_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail="agent not found")
    return status


@router.post("/api/agents/{agent_id}/approve")
async def approve_agent(agent_id: str, request: ApprovalRequest) -> dict[str, Any]:
    orchestrator = get_orchestrator()
    try:
        await orchestrator.approve(agent_id, request.approved)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"agent_id": agent_id, "approved": request.approved}


@router.post("/api/agents/{agent_id}/cancel")
async def cancel_agent(agent_id: str) -> dict[str, Any]:
    orchestrator = get_orchestrator()
    try:
        await orchestrator.cancel_agent(agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"agent_id": agent_id, "status": "cancelled"}
