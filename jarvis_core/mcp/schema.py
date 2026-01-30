"""Schema definitions for MCP servers and tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MCPServerStatus(Enum):
    """Connection status for MCP servers."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class MCPTool:
    """Tool metadata exposed by an MCP server."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    required_params: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class MCPServer:
    """MCP server definition."""

    name: str
    server_url: str
    server_type: str
    tools: list[MCPTool] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    status: MCPServerStatus = MCPServerStatus.DISCONNECTED
    requests_per_minute: int | None = None


@dataclass
class MCPToolResult:
    """Result of invoking an MCP tool."""

    tool_name: str
    server_name: str
    success: bool
    data: Any = None
    error: str | None = None
    latency_ms: float | None = None