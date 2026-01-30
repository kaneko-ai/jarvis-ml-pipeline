import pytest

from jarvis_core.mcp.chain import ToolChain
from jarvis_core.mcp.schema import MCPToolResult


class DummyHub:
    def __init__(self, results):
        self._results = results
        self.calls = []

    async def invoke_tool(self, tool_name, params):
        self.calls.append((tool_name, params))
        return self._results.pop(0)


@pytest.mark.asyncio
async def test_tool_chain_executes_steps():
    results = [
        MCPToolResult(
            tool_name="first",
            server_name="srv",
            success=True,
            data={"ids": ["A", "B"]},
        ),
        MCPToolResult(
            tool_name="second",
            server_name="srv",
            success=True,
            data={"status": "ok"},
        ),
    ]
    hub = DummyHub(results)
    chain = ToolChain(hub)
    chain.add_step("first", lambda initial, _: {"query": initial["query"]})
    chain.add_step("second", lambda previous, _: {"ids": previous["ids"]})

    output = await chain.execute({"query": "cats"})

    assert [result.tool_name for result in output] == ["first", "second"]
    assert hub.calls == [
        ("first", {"query": "cats"}),
        ("second", {"ids": ["A", "B"]}),
    ]


@pytest.mark.asyncio
async def test_tool_chain_continue_on_error():
    results = [
        MCPToolResult(
            tool_name="first",
            server_name="srv",
            success=True,
            data={"next": "value"},
        ),
        MCPToolResult(
            tool_name="second",
            server_name="srv",
            success=False,
            data={"fallback": True},
            error="boom",
        ),
        MCPToolResult(
            tool_name="third",
            server_name="srv",
            success=True,
            data={"done": True},
        ),
    ]
    hub = DummyHub(results)
    chain = ToolChain(hub, continue_on_error=True)
    chain.add_step("first", lambda initial, _: {"seed": initial["seed"]})
    chain.add_step("second", lambda previous, _: {"next": previous["next"]})
    chain.add_step("third", lambda previous, _: {"fallback": previous.get("fallback", False)})

    output = await chain.execute({"seed": "alpha"})

    assert [result.tool_name for result in output] == ["first", "second", "third"]