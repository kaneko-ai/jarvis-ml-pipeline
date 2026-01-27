"""Inbox API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jarvis_web.api.orchestrator import _ensure_started, _get_orchestrator


router = APIRouter(prefix="/api", tags=["inbox"])


class ConversationCreateRequest(BaseModel):
    title: str
    workspace: str


class MessageCreateRequest(BaseModel):
    agent_id: str
    role: str
    content: str
    artifacts: list[str] | None = None


@router.get("/inbox")
async def get_inbox() -> dict[str, Any]:
    orchestrator = _get_orchestrator()
    return {"inbox": orchestrator.get_inbox()}


@router.post("/conversations")
async def create_conversation(payload: ConversationCreateRequest) -> dict[str, Any]:
    orchestrator = await _ensure_started()
    conversation_id = orchestrator.create_conversation(payload.title, payload.workspace)
    return {"conversation_id": conversation_id}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict[str, Any]:
    orchestrator = _get_orchestrator()
    conversation = orchestrator.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation_not_found")
    return {"conversation": conversation}


@router.post("/conversations/{conversation_id}/messages")
async def add_message(conversation_id: str, payload: MessageCreateRequest) -> dict[str, Any]:
    orchestrator = _get_orchestrator()
    try:
        message_id = orchestrator.add_message(
            conversation_id,
            agent_id=payload.agent_id,
            role=payload.role,
            content=payload.content,
            artifacts=payload.artifacts,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="conversation_not_found")
    return {"message_id": message_id}
