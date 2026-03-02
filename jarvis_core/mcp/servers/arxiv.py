"""arXiv MCP server definition."""

from __future__ import annotations

from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


def get_arxiv_mcp_server() -> MCPServer:
    """Return a preconfigured MCP server definition for arXiv."""
    tools = [
        MCPTool(
            name="arxiv_search",
            description="Search arXiv papers by query.",
            parameters={
                "query": "string",
                "max_results": "integer",
                "category": "string",
            },
            required_params=["query"],
        ),
        MCPTool(
            name="arxiv_fetch",
            description="Fetch an arXiv paper by ID.",
            parameters={
                "arxiv_id": "string",
            },
            required_params=["arxiv_id"],
        ),
    ]

    return MCPServer(
        name="arxiv",
        server_url="http://export.arxiv.org/api",
        server_type="rest",
        tools=tools,
        headers={"Accept": "application/xml"},
        status=MCPServerStatus.DISCONNECTED,
        requests_per_minute=20,
    )
