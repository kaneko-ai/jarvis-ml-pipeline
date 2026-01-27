"""Predefined MCP server definitions."""

from .openalex import get_openalex_mcp_server
from .pubmed import get_pubmed_mcp_server
from .semantic_scholar import get_semantic_scholar_mcp_server

__all__ = [
    "get_openalex_mcp_server",
    "get_pubmed_mcp_server",
    "get_semantic_scholar_mcp_server",
]
