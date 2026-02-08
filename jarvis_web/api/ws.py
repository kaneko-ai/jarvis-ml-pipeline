"""WebSocket endpoints for agent progress."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from jarvis_web.api.orchestrator import _ensure_started


router = APIRouter()


@router.websocket("/ws/agents/{agent_id}")
async def agent_progress(websocket: WebSocket, agent_id: str) -> None:
    await websocket.accept()
    orchestrator = await _ensure_started()

    async def send_event(event_type: str, payload: dict) -> None:
        if payload.get("agent_id") != agent_id:
            return
        try:
            await websocket.send_json({"event": event_type, "data": payload})
        except WebSocketDisconnect:
            return

    async def status_callback(payload: dict) -> None:
        await send_event("status_change", payload)

    async def progress_callback(payload: dict) -> None:
        await send_event("progress_update", payload)

    async def artifact_callback(payload: dict) -> None:
        await send_event("artifact_created", payload)

    async def approval_callback(payload: dict) -> None:
        await send_event("approval_required", payload)

    orchestrator.register_callback("status_change", status_callback)
    orchestrator.register_callback("progress_update", progress_callback)
    orchestrator.register_callback("artifact_created", artifact_callback)
    orchestrator.register_callback("approval_required", approval_callback)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return


def _load_run_status(run_id: str) -> str:
    """Return run status if available, otherwise unknown."""
    run_paths = [
        Path("data/runs") / run_id / "result.json",
        Path("logs/runs") / run_id / "result.json",
    ]
    for result_path in run_paths:
        if not result_path.exists():
            continue
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        status = str(payload.get("status", "")).strip().lower()
        return status or "unknown"
    return "unknown"


@router.websocket("/ws/runs/{run_id}")
async def run_progress(websocket: WebSocket, run_id: str) -> None:
    """WebSocket endpoint for run progress updates."""
    await websocket.accept()
    await websocket.send_json({"event": "connected", "data": {"run_id": run_id}})
    await websocket.send_json(
        {"event": "run_status", "data": {"run_id": run_id, "status": _load_run_status(run_id)}}
    )

    try:
        while True:
            message = await websocket.receive_text()
            if message.strip().lower() == "ping":
                await websocket.send_json({"event": "pong", "data": {"run_id": run_id}})
    except WebSocketDisconnect:
        return
