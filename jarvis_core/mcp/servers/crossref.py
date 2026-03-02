"""Crossref MCP server definition."""

from __future__ import annotations

from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


def get_crossref_mcp_server() -> MCPServer:
    """Return a preconfigured MCP server definition for Crossref."""
    tools = [
        MCPTool(
            name="crossref_search",
            description="Search Crossref works by query.",
            parameters={
                "query": "string",
                "rows": "integer",
                "filter_type": "string",
            },
            required_params=["query"],
        ),
        MCPTool(
            name="crossref_doi",
            description="Fetch Crossref metadata by DOI.",
            parameters={
                "doi": "string",
            },
            required_params=["doi"],
        ),
    ]

    return MCPServer(
        name="crossref",
        server_url="https://api.crossref.org",
        server_type="rest",
        tools=tools,
        headers={"User-Agent": "JARVIS Research OS/1.0 (mailto:jarvis@example.com)"},
        status=MCPServerStatus.DISCONNECTED,
        requests_per_minute=50,
    )
