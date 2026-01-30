"""OpenAlex MCP server definition."""

from __future__ import annotations

from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


def get_openalex_mcp_server() -> MCPServer:
    """Return a preconfigured MCP server definition for OpenAlex."""
    tools = [
        MCPTool(
            name="openalex_search",
            description="Search OpenAlex works by query.",
            parameters={
                "query": "string",
                "filter": "string",
                "sort": "string",
            },
            required_params=["query"],
        ),
        MCPTool(
            name="openalex_work",
            description="Fetch an OpenAlex work by ID.",
            parameters={
                "work_id": "string",
            },
            required_params=["work_id"],
        ),
        MCPTool(
            name="openalex_author",
            description="Fetch an OpenAlex author by ID.",
            parameters={
                "author_id": "string",
            },
            required_params=["author_id"],
        ),
        MCPTool(
            name="openalex_institution",
            description="Fetch an OpenAlex institution by ID.",
            parameters={
                "institution_id": "string",
            },
            required_params=["institution_id"],
        ),
    ]

    return MCPServer(
        name="openalex",
        server_url="https://api.openalex.org",
        server_type="rest",
        tools=tools,
        headers={"Accept": "application/json"},
        status=MCPServerStatus.DISCONNECTED,
        requests_per_minute=100,
    )
