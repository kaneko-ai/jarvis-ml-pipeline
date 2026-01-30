"""PubMed MCP server definition."""

from __future__ import annotations

from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool


def get_pubmed_mcp_server() -> MCPServer:
    """Return a preconfigured MCP server definition for PubMed."""
    tools = [
        MCPTool(
            name="pubmed_search",
            description="Search PubMed by query.",
            parameters={
                "query": "string",
                "max_results": "integer",
                "date_range": "string",
            },
            required_params=["query"],
        ),
        MCPTool(
            name="pubmed_fetch",
            description="Fetch PubMed records by PMIDs.",
            parameters={
                "pmids": "list[string]",
            },
            required_params=["pmids"],
        ),
        MCPTool(
            name="pubmed_citations",
            description="Fetch citation data for a PubMed ID.",
            parameters={
                "pmid": "string",
            },
            required_params=["pmid"],
        ),
    ]

    return MCPServer(
        name="pubmed",
        server_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
        server_type="rest",
        tools=tools,
        headers={"Accept": "application/json"},
        status=MCPServerStatus.DISCONNECTED,
        requests_per_minute=30,
    )
