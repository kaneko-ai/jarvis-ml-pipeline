# MCP Config Guide

This document describes the JSON format used by `MCPHub.register_from_config()` for loading MCP servers.

## Example

```json
{
  "mcpServers": {
    "pubmed": {
      "serverUrl": "https://example-mcp.pubmed.org",
      "type": "http",
      "headers": {
        "User-Agent": "jarvis-mcp/1.0"
      },
      "requests_per_minute": 30
    }
  }
}
```

## Fields

- `mcpServers`: Object map of server name to configuration.
- `serverUrl`: Base URL for the MCP server.
- `type`: Server type descriptor (e.g., `http`).
- `headers`: Optional HTTP headers to include with requests.
- `requests_per_minute`: Optional rate limit applied by the hub.
- `tools`: Optional list of tool definitions if you want to pre-register tools.

Each tool object may include:

- `name`
- `description`
- `parameters`
- `required_params`
- `enabled`
