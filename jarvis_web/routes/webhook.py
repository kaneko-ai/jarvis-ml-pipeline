"""Webhook receiver for observability testing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api/obs", tags=["observability"])


@router.post("/webhook/test")
async def webhook_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
