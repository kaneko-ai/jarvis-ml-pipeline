"""Benchmark MCP hub performance metrics."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from jarvis_core.mcp.hub import MCPHub
from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


@dataclass
class _FakeResponse:
    payload: dict

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _mock_request(method, url, headers=None, json=None, timeout=None):
    if url.endswith("/tools"):
        return _FakeResponse(payload={"tools": [{"name": "search", "description": "Search"}]})
    return _FakeResponse(payload={"ok": True, "result": json})


async def _run_discovery(hub: MCPHub, server: MCPServer) -> float:
    start = time.perf_counter()
    await hub.discover_tools(server.name)
    return (time.perf_counter() - start) * 1000


async def _run_invoke(hub: MCPHub) -> float:
    start = time.perf_counter()
    await hub.invoke_tool("search", {"query": "benchmark"})
    return (time.perf_counter() - start) * 1000


async def _run_parallel(hub: MCPHub, n: int) -> float:
    start = time.perf_counter()
    await asyncio.gather(*(hub.invoke_tool("search", {"query": f"q{i}"}) for i in range(n)))
    elapsed = time.perf_counter() - start
    return n / elapsed if elapsed > 0 else 0.0


def run_benchmark(output_path: str = "results/mcp_benchmark.json") -> dict:
    """Run MCP performance benchmark and write results."""
    hub = MCPHub()
    server = MCPServer(
        name="benchmark",
        server_url="https://mcp.mock",
        server_type="http",
        headers={},
        status=MCPServerStatus.DISCONNECTED,
    )
    server.tools = [MCPTool(name="search", description="Search", parameters={}, required_params=[], enabled=True)]
    hub.register_server(server)

    original_request = requests.request
    requests.request = _mock_request
    try:
        discovery_ms = asyncio.run(_run_discovery(hub, server))
        invoke_ms = asyncio.run(_run_invoke(hub))
        throughput = asyncio.run(_run_parallel(hub, 10))
    finally:
        requests.request = original_request

    results = {
        "tool_discovery_latency_ms": discovery_ms,
        "tool_execution_latency_ms": invoke_ms,
        "parallel_throughput_rps": throughput,
        "sample_size": 10,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main():
    results = run_benchmark()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
