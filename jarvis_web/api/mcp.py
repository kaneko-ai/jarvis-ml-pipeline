"""MCP API endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from jarvis_core.mcp.hub import MCPHub


router = APIRouter()
_hub = MCPHub()
_loaded = False


def _ensure_loaded() -> MCPHub:
    global _loaded
    if not _loaded:
        config_path = Path("configs/mcp_config.json")
        if config_path.exists():
            _hub.register_from_config(str(config_path))
        _loaded = True
    return _hub


@router.get("/api/mcp/servers")
async def list_servers() -> list[dict[str, Any]]:
    hub = _ensure_loaded()
    return hub.list_servers()


@router.get("/api/mcp/tools")
async def list_tools() -> list[dict[str, Any]]:
    hub = _ensure_loaded()
    return hub.list_all_tools()


@router.post("/api/mcp/tools/{tool_name}/invoke")
async def invoke_tool(tool_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    hub = _ensure_loaded()
    result = await hub.invoke_tool(tool_name, params or {})
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "tool invocation failed")
    return result.__dict__


@router.post("/api/mcp/discover/{server_name}")
async def discover_tools(server_name: str) -> list[dict[str, Any]]:
    hub = _ensure_loaded()
    tools = await hub.discover_tools(server_name)
    return [tool.__dict__ for tool in tools]
