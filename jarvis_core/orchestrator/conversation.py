"""Conversation (Inbox) schemas for orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ConversationMessage:
    message_id: str
    agent_id: str
    role: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    artifacts: list[str] = field(default_factory=list)


@dataclass
class Conversation:
    conversation_id: str
    title: str
    workspace: str
    agents: list[str] = field(default_factory=list)
    messages: list[ConversationMessage] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
