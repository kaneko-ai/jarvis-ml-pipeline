"""Semantic Scholar MCP server definition."""

from __future__ import annotations

from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


def get_semantic_scholar_mcp_server() -> MCPServer:
    """Return a preconfigured MCP server definition for Semantic Scholar."""
    tools = [
        MCPTool(
            name="s2_search",
            description="Search Semantic Scholar by query.",
            parameters={
                "query": "string",
                "fields": "list[string]",
                "limit": "integer",
            },
            required_params=["query"],
        ),
        MCPTool(
            name="s2_paper",
            description="Fetch a paper by Semantic Scholar paper ID.",
            parameters={
                "paper_id": "string",
            },
            required_params=["paper_id"],
        ),
        MCPTool(
            name="s2_citations",
            description="Fetch citations for a Semantic Scholar paper.",
            parameters={
                "paper_id": "string",
                "limit": "integer",
            },
            required_params=["paper_id"],
        ),
        MCPTool(
            name="s2_references",
            description="Fetch references for a Semantic Scholar paper.",
            parameters={
                "paper_id": "string",
                "limit": "integer",
            },
            required_params=["paper_id"],
        ),
    ]

    return MCPServer(
        name="semantic_scholar",
        server_url="https://api.semanticscholar.org/graph/v1",
        server_type="rest",
        tools=tools,
        headers={"Accept": "application/json"},
        status=MCPServerStatus.DISCONNECTED,
        requests_per_minute=100,
    )