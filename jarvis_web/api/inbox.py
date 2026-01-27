"""Inbox API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jarvis_web.api.state import get_orchestrator


router = APIRouter()


class ConversationCreateRequest(BaseModel):
    """Request to create a conversation."""

    title: str = Field(..., description="Conversation title.")
    workspace: str = Field(..., description="Workspace identifier.")


class MessageCreateRequest(BaseModel):
    """Request to add a message to a conversation."""

    agent_id: str = Field(..., description="Agent ID.")
    role: str = Field(..., description="Message role.")
    content: str = Field(..., description="Message content.")
    artifacts: list[str] = Field(default_factory=list, description="Artifact paths.")


@router.get("/api/inbox")
async def list_conversations() -> list[dict[str, Any]]:
    orchestrator = get_orchestrator()
    return orchestrator.get_inbox()


@router.post("/api/conversations")
async def create_conversation(request: ConversationCreateRequest) -> dict[str, Any]:
    orchestrator = get_orchestrator()
    conversation_id = orchestrator.create_conversation(request.title, request.workspace)
    return {"conversation_id": conversation_id}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict[str, Any]:
    orchestrator = get_orchestrator()
    conversation = orchestrator.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "workspace": conversation.workspace,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": message.id,
                "agent_id": message.agent_id,
                "role": message.role,
                "content": message.content,
                "artifacts": message.artifacts,
                "created_at": message.created_at.isoformat(),
            }
            for message in conversation.messages
        ],
    }


@router.post("/api/conversations/{conversation_id}/messages")
async def add_message(
    conversation_id: str, request: MessageCreateRequest
) -> dict[str, Any]:
    orchestrator = get_orchestrator()
    try:
        message_id = orchestrator.add_message(
            conversation_id,
            request.agent_id,
            request.role,
            request.content,
            request.artifacts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message_id": message_id}
