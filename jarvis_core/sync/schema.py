from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class QueueItemStatus(Enum):
    """Status of a sync queue item."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class QueueItem:
    """An item in the sync queue."""
    id: str  # Renamed from item_id to match instructions/preference or keep simple? Kept 'id' as per instruction
    operation: str
    params: dict[str, Any] # Renamed from payload to match instruction
    status: QueueItemStatus = QueueItemStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    error: str | None = None # Renamed from error_message
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "operation": self.operation,
            "params": self.params,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error": self.error,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueueItem:
        return cls(
            id=data["id"],
            operation=data["operation"],
            params=data.get("params", {}),
            status=QueueItemStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error=data.get("error"),
            result=data.get("result"),
        )
