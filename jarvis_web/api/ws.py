"""WebSocket endpoints for agent progress."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from jarvis_web.api.state import get_orchestrator


router = APIRouter()


@router.websocket("/ws/agents/{agent_id}")
async def agent_ws(websocket: WebSocket, agent_id: str) -> None:
    orchestrator = get_orchestrator()
    await websocket.accept()

    def make_callback(event_type: str):
        async def _callback(payload: dict) -> None:
            if payload.get("agent_id") != agent_id:
                return
            await websocket.send_json({"event": event_type, **payload})

        return _callback

    unsubscribe = []
    for event_type in [
        "status_change",
        "progress_update",
        "artifact_created",
        "approval_required",
    ]:
        callback = make_callback(event_type)
        unsubscribe.append(orchestrator.register_callback(event_type, callback))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        for unsub in unsubscribe:
            unsub()
