from jarvis_core.mcp.servers.pubmed import get_pubmed_mcp_server


def test_pubmed_server_definition():
    server = get_pubmed_mcp_server()

    tool_names = {tool.name for tool in server.tools}
    assert tool_names == {"pubmed_search", "pubmed_fetch", "pubmed_citations"}
    assert server.requests_per_minute == 30