from dataclasses import dataclass

import pytest
import requests

from async_test_utils import run_async
from jarvis_core.mcp.chain import ToolChain
from jarvis_core.mcp.hub import MCPHub
from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


@dataclass
class _FakeResponse:
    status_code: int = 200
    payload: dict | list | None = None

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"Status {self.status_code}")

    def json(self):
        return self.payload


@pytest.mark.integration
def test_mcp_server_registration_and_discovery(monkeypatch):
    hub = MCPHub()
    server = MCPServer(
        name="mock",
        server_url="https://mcp.example",
        server_type="http",
        headers={},
        status=MCPServerStatus.DISCONNECTED,
    )
    hub.register_server(server)

    def fake_request(method, url, headers=None, timeout=None):
        assert method == "GET"
        assert url.endswith("/tools")
        return _FakeResponse(payload={"tools": [{"name": "search", "description": "Search"}]})

    monkeypatch.setattr(requests, "request", fake_request)
    tools = run_async(hub.discover_tools("mock"))

    assert tools[0].name == "search"
    assert server.status == MCPServerStatus.CONNECTED


@pytest.mark.integration
def test_mcp_tool_invoke_and_error(monkeypatch):
    hub = MCPHub()
    server = MCPServer(
        name="mock",
        server_url="https://mcp.example",
        server_type="http",
        headers={},
        status=MCPServerStatus.DISCONNECTED,
    )
    server.tools = [
        MCPTool(
            name="search", description="Search", parameters={}, required_params=[], enabled=True
        )
    ]
    hub.register_server(server)

    def fake_success(method, url, headers=None, json=None, timeout=None):
        assert method == "POST"
        return _FakeResponse(payload={"items": ["ok"]})

    monkeypatch.setattr(requests, "request", fake_success)
    result = run_async(hub.invoke_tool("search", {"query": "ok"}))
    assert result.success is True
    assert result.data == {"items": ["ok"]}

    def fake_fail(method, url, headers=None, json=None, timeout=None):
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "request", fake_fail)
    result = run_async(hub.invoke_tool("search", {"query": "fail"}))
    assert result.success is False
    assert result.error is not None


@pytest.mark.integration
def test_mcp_rate_limiting(monkeypatch):
    hub = MCPHub()
    server = MCPServer(
        name="rate",
        server_url="https://mcp.example",
        server_type="http",
        headers={},
        status=MCPServerStatus.DISCONNECTED,
        requests_per_minute=1,
    )
    server.tools = [
        MCPTool(
            name="search", description="Search", parameters={}, required_params=[], enabled=True
        )
    ]
    hub.register_server(server)

    def fake_success(method, url, headers=None, json=None, timeout=None):
        return _FakeResponse(payload={"items": ["ok"]})

    monkeypatch.setattr(requests, "request", fake_success)
    first = run_async(hub.invoke_tool("search", {"query": "one"}))
    second = run_async(hub.invoke_tool("search", {"query": "two"}))

    assert first.success is True
    assert second.success is False
    assert second.error == "rate_limit_exceeded"


@pytest.mark.integration
def test_mcp_tool_chain(monkeypatch):
    hub = MCPHub()
    server = MCPServer(
        name="chain",
        server_url="https://mcp.example",
        server_type="http",
        headers={},
        status=MCPServerStatus.DISCONNECTED,
    )
    server.tools = [
        MCPTool(
            name="step_one", description="Step 1", parameters={}, required_params=[], enabled=True
        ),
        MCPTool(
            name="step_two", description="Step 2", parameters={}, required_params=[], enabled=True
        ),
    ]
    hub.register_server(server)

    def fake_success(method, url, headers=None, json=None, timeout=None):
        tool_name = json.get("tool")
        if tool_name == "step_one":
            return _FakeResponse(payload={"value": 1})
        return _FakeResponse(payload={"value": json["params"]["value"] + 1})

    monkeypatch.setattr(requests, "request", fake_success)

    chain = ToolChain(hub)
    chain.add_step("step_one", lambda initial, results: {"query": initial["query"]})
    chain.add_step("step_two", lambda _initial, results: {"value": results[-1].data["value"]})

    results = run_async(chain.execute({"query": "start"}))
    assert results[-1].data["value"] == 2
