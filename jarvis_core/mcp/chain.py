"""Tool chaining utilities for MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .hub import MCPHub
from .schema import MCPToolResult


class ToolChain:
    """Chain multiple MCP tools with input mapping between steps."""

    def __init__(self, hub: MCPHub, continue_on_error: bool = False) -> None:
        self._hub = hub
        self._steps: list[tuple[str, Callable[[dict[str, Any], list[MCPToolResult]], dict[str, Any]]]] = []
        self._continue_on_error = continue_on_error

    def add_step(
        self,
        tool_name: str,
        params_mapper: Callable[[dict[str, Any], list[MCPToolResult]], dict[str, Any]],
    ) -> None:
        """Add a tool step with a params mapper."""
        self._steps.append((tool_name, params_mapper))

    def set_continue_on_error(self, continue_on_error: bool) -> None:
        """Set whether to continue execution after errors."""
        self._continue_on_error = continue_on_error

    async def execute(self, initial_input: dict[str, Any]) -> list[MCPToolResult]:
        """Execute the tool chain sequentially."""
        current_input = initial_input
        results: list[MCPToolResult] = []
        for tool_name, mapper in self._steps:
            params = mapper(current_input, results)
            result = await self._hub.invoke_tool(tool_name, params)
            results.append(result)
            if not result.success and not self._continue_on_error:
                break
            if isinstance(result.data, dict):
                current_input = result.data
            else:
                current_input = {"result": result.data}
        return results
