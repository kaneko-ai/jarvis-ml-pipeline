import pytest

from async_test_utils import sync_async_test
from jarvis_core.mcp.hub import MCPHub
from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


@sync_async_test
async def test_discover_and_invoke_tools(monkeypatch):
    hub = MCPHub()
    server = MCPServer(
        name="alpha",
        server_url="https://example.com/mcp",
        server_type="http",
    )
    hub.register_server(server)

    responses = [
        DummyResponse(
            {
                "tools": [
                    {
                        "name": "search",
                        "description": "Search tool",
                        "parameters": {"query": "string"},
                        "required_params": ["query"],
                        "enabled": True,
                    }
                ]
            }
        ),
        DummyResponse({"result": "ok"}),
    ]

    def fake_request(method, url, headers=None, json=None, timeout=30):
        return responses.pop(0)

    monkeypatch.setattr("requests.request", fake_request)

    tools = await hub.discover_tools("alpha")
    assert tools
    assert tools[0].name == "search"
    assert server.status == MCPServerStatus.CONNECTED

    result = await hub.invoke_tool("search", {"query": "cats"})
    assert result.success is True
    assert result.data == {"result": "ok"}

    listing = hub.list_all_tools()
    assert listing == [
        {
            "server": "alpha",
            "tool": "search",
            "description": "Search tool",
            "enabled": True,
            "required_params": ["query"],
        }
    ]


@sync_async_test
async def test_rate_limit_exceeded(monkeypatch):
    hub = MCPHub()
    server = MCPServer(
        name="rate",
        server_url="https://example.com/mcp",
        server_type="http",
        tools=[MCPTool(name="tool", description="", parameters={})],
        requests_per_minute=1,
    )
    hub.register_server(server)

    def fake_request(method, url, headers=None, json=None, timeout=30):
        return DummyResponse({"result": "ok"})

    monkeypatch.setattr("requests.request", fake_request)

    result = await hub.invoke_tool("tool", {})
    assert result.success is True

    limited = await hub.invoke_tool("tool", {})
    assert limited.success is False
    assert limited.error == "rate_limit_exceeded"
