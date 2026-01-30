"""Core hub for managing MCP servers and invoking tools."""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

from .schema import MCPServer, MCPServerStatus, MCPTool, MCPToolResult


class MCPHub:
    """Hub that registers MCP servers and invokes tools."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServer] = {}
        self._rate_log: dict[str, list[float]] = defaultdict(list)

    def register_server(self, server: MCPServer) -> None:
        """Register an MCP server."""
        self._servers[server.name] = server

    def register_from_config(self, config_path: str) -> None:
        """Register MCP servers from a JSON configuration file."""
        path = Path(config_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        for name, payload in servers.items():
            server = MCPServer(
                name=name,
                server_url=payload.get("serverUrl", ""),
                server_type=payload.get("type", "http"),
                headers=payload.get("headers", {}),
                status=MCPServerStatus.DISCONNECTED,
                requests_per_minute=payload.get("requests_per_minute"),
            )
            tool_defs = payload.get("tools", [])
            if tool_defs:
                server.tools = [
                    MCPTool(
                        name=tool.get("name", ""),
                        description=tool.get("description", ""),
                        parameters=tool.get("parameters", {}),
                        required_params=tool.get("required_params", []),
                        enabled=tool.get("enabled", True),
                    )
                    for tool in tool_defs
                ]
            self.register_server(server)

    async def discover_tools(self, server_name: str) -> list[MCPTool]:
        """Discover tools from a specific server."""
        server = self._servers.get(server_name)
        if not server:
            return []
        if not self._allow_request(server):
            server.status = MCPServerStatus.RATE_LIMITED
            return []

        url = f"{server.server_url.rstrip('/')}/tools"
        start = time.perf_counter()
        try:
            response = await asyncio.to_thread(
                requests.request,
                "GET",
                url,
                headers=server.headers,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            tool_payloads = payload.get("tools", payload if isinstance(payload, list) else [])
            tools = [
                MCPTool(
                    name=tool.get("name", ""),
                    description=tool.get("description", ""),
                    parameters=tool.get("parameters", {}),
                    required_params=tool.get("required_params", []),
                    enabled=tool.get("enabled", True),
                )
                for tool in tool_payloads
            ]
            server.tools = tools
            server.status = MCPServerStatus.CONNECTED
            _ = (time.perf_counter() - start) * 1000
            return tools
        except requests.RequestException:
            server.status = MCPServerStatus.ERROR
            return []

    async def invoke_tool(self, tool_name: str, params: dict) -> MCPToolResult:
        """Invoke a tool by name using the registered servers."""
        server, tool = self._find_tool(tool_name)
        if not server or not tool:
            return MCPToolResult(
                tool_name=tool_name,
                server_name=server.name if server else "unknown",
                success=False,
                error="tool_not_found",
                latency_ms=0.0,
            )
        if not tool.enabled:
            return MCPToolResult(
                tool_name=tool_name,
                server_name=server.name,
                success=False,
                error="tool_disabled",
                latency_ms=0.0,
            )
        if not self._allow_request(server):
            server.status = MCPServerStatus.RATE_LIMITED
            return MCPToolResult(
                tool_name=tool_name,
                server_name=server.name,
                success=False,
                error="rate_limit_exceeded",
                latency_ms=0.0,
            )

        url = f"{server.server_url.rstrip('/')}/invoke"
        payload = {"tool": tool_name, "params": params}
        start = time.perf_counter()
        try:
            response = await asyncio.to_thread(
                requests.request,
                "POST",
                url,
                headers=server.headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.perf_counter() - start) * 1000
            server.status = MCPServerStatus.CONNECTED
            return MCPToolResult(
                tool_name=tool_name,
                server_name=server.name,
                success=True,
                data=data,
                latency_ms=latency_ms,
            )
        except requests.RequestException as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            server.status = MCPServerStatus.ERROR
            return MCPToolResult(
                tool_name=tool_name,
                server_name=server.name,
                success=False,
                error=str(exc),
                latency_ms=latency_ms,
            )

    def list_all_tools(self) -> list[dict[str, Any]]:
        """List all registered tools across servers."""
        tools: list[dict[str, Any]] = []
        for server in self._servers.values():
            for tool in server.tools:
                tools.append(
                    {
                        "server": server.name,
                        "tool": tool.name,
                        "description": tool.description,
                        "enabled": tool.enabled,
                        "required_params": tool.required_params,
                    }
                )
        return tools

    def list_servers(self) -> list[dict[str, Any]]:
        """List registered MCP servers."""
        return [
            {
                "name": server.name,
                "server_url": server.server_url,
                "server_type": server.server_type,
                "status": server.status.value,
                "tool_count": len(server.tools),
            }
            for server in self._servers.values()
        ]

    def _find_tool(self, tool_name: str) -> tuple[MCPServer | None, MCPTool | None]:
        for server in self._servers.values():
            for tool in server.tools:
                if tool.name == tool_name:
                    return server, tool
        return None, None

    def _allow_request(self, server: MCPServer) -> bool:
        if not server.requests_per_minute:
            return True
        now = time.time()
        window_start = now - 60
        timestamps = [t for t in self._rate_log[server.name] if t >= window_start]
        self._rate_log[server.name] = timestamps
        if len(timestamps) >= server.requests_per_minute:
            return False
        timestamps.append(now)
        self._rate_log[server.name] = timestamps
        return True