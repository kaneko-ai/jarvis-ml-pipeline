"""MCP API endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from jarvis_core.mcp.hub import MCPHub


router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class ToolInvokeRequest(BaseModel):
    params: dict[str, Any] = {}


_hub: MCPHub | None = None


def _get_hub() -> MCPHub:
    global _hub
    if _hub is None:
        hub = MCPHub()
        config_path = Path("configs/mcp_config.json")
        if config_path.exists():
            hub.register_from_config(str(config_path))
        _hub = hub
    return _hub


@router.get("/servers")
async def list_servers() -> dict[str, Any]:
    hub = _get_hub()
    return {"servers": hub.list_servers()}


@router.get("/tools")
async def list_tools() -> dict[str, Any]:
    hub = _get_hub()
    return {"tools": hub.list_all_tools()}


@router.post("/tools/{tool_name}/invoke")
async def invoke_tool(tool_name: str, payload: ToolInvokeRequest) -> dict[str, Any]:
    hub = _get_hub()
    result = await hub.invoke_tool(tool_name, payload.params)
    return {"result": result.__dict__}


@router.post("/discover/{server_name}")
async def discover_tools(server_name: str) -> dict[str, Any]:
    hub = _get_hub()
    tools = await hub.discover_tools(server_name)
    return {"tools": [tool.__dict__ for tool in tools]}
