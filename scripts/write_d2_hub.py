import pathlib

target = pathlib.Path("jarvis_core/mcp/hub.py")

code = '''\
"""Core hub for managing MCP servers and invoking tools."""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

from .schema import MCPServer, MCPServerStatus, MCPTool, MCPToolResult


class MCPHub:
    """Hub that registers MCP servers and invokes tools."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServer] = {}
        self._rate_log: dict[str, list[float]] = defaultdict(list)
        self._local_handlers: dict[str, Any] = {}

    def register_server(self, server: MCPServer) -> None:
        """Register an MCP server."""
        self._servers[server.name] = server

    def register_builtin_servers(self) -> None:
        """Register all predefined builtin MCP servers."""
        from .servers import (
            get_pubmed_mcp_server,
            get_openalex_mcp_server,
            get_semantic_scholar_mcp_server,
            get_arxiv_mcp_server,
            get_crossref_mcp_server,
        )
        for factory in [
            get_pubmed_mcp_server,
            get_openalex_mcp_server,
            get_semantic_scholar_mcp_server,
            get_arxiv_mcp_server,
            get_crossref_mcp_server,
        ]:
            server = factory()
            self.register_server(server)

    def register_local_handler(self, tool_name: str, handler: Any) -> None:
        """Register a local Python callable as a tool handler."""
        self._local_handlers[tool_name] = handler

    def register_from_config(self, config_path: str) -> None:
        """Register MCP servers from a JSON configuration file."""
        path = Path(config_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        for name, payload in servers.items():
            server = MCPServer(
                name=name,
                server_url=payload.get("serverUrl", ""),
                server_type=payload.get("type", "http"),
                headers=payload.get("headers", {}),
                status=MCPServerStatus.DISCONNECTED,
                requests_per_minute=payload.get("requests_per_minute"),
            )
            tool_defs = payload.get("tools", [])
            if tool_defs:
                server.tools = [
                    MCPTool(
                        name=tool.get("name", ""),
                        description=tool.get("description", ""),
                        parameters=tool.get("parameters", {}),
                        required_params=tool.get("required_params", []),
                        enabled=tool.get("enabled", True),
                    )
                    for tool in tool_defs
                ]
            self.register_server(server)

    def invoke_tool_sync(self, tool_name: str, params: dict) -> MCPToolResult:
        """Synchronously invoke a tool - tries local handler first, then remote."""
        # Try local handler
        handler = self._local_handlers.get(tool_name)
        if handler:
            start = time.perf_counter()
            try:
                data = handler(params)
                latency = (time.perf_counter() - start) * 1000
                return MCPToolResult(
                    tool_name=tool_name,
                    server_name="local",
                    success=True,
                    data=data,
                    latency_ms=latency,
                )
            except Exception as e:
                latency = (time.perf_counter() - start) * 1000
                return MCPToolResult(
                    tool_name=tool_name,
                    server_name="local",
                    success=False,
                    error=str(e),
                    latency_ms=latency,
                )

        # Find the tool in registered servers
        server, tool = self._find_tool(tool_name)
        if not server or not tool:
            return MCPToolResult(
                tool_name=tool_name,
                server_name="unknown",
                success=False,
                error="tool_not_found",
                latency_ms=0.0,
            )

        # Dispatch to known API handlers
        dispatch = {
            "pubmed_search": self._local_pubmed_search,
            "arxiv_search": self._local_arxiv_search,
            "crossref_search": self._local_crossref_search,
            "crossref_doi": self._local_crossref_doi,
            "openalex_search": self._local_openalex_search,
            "openalex_work": self._local_openalex_work,
            "s2_search": self._local_s2_search,
            "s2_paper": self._local_s2_paper,
            "s2_citations": self._local_s2_citations,
            "s2_references": self._local_s2_references,
        }
        local_fn = dispatch.get(tool_name)
        if local_fn:
            start = time.perf_counter()
            try:
                data = local_fn(params)
                latency = (time.perf_counter() - start) * 1000
                server.status = MCPServerStatus.CONNECTED
                return MCPToolResult(
                    tool_name=tool_name,
                    server_name=server.name,
                    success=True,
                    data=data,
                    latency_ms=latency,
                )
            except Exception as e:
                latency = (time.perf_counter() - start) * 1000
                server.status = MCPServerStatus.ERROR
                return MCPToolResult(
                    tool_name=tool_name,
                    server_name=server.name,
                    success=False,
                    error=str(e),
                    latency_ms=latency,
                )

        return MCPToolResult(
            tool_name=tool_name,
            server_name=server.name,
            success=False,
            error="no_local_handler_and_remote_not_available",
            latency_ms=0.0,
        )

    # --- Local API handlers: PubMed ---

    def _local_pubmed_search(self, params: dict) -> dict:
        from jarvis_core.sources import PubMedClient
        client = PubMedClient()
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        articles = client.search(query, max_results=max_results)
        results = []
        for a in articles:
            if isinstance(a, dict):
                results.append({"title": a.get("title", ""), "pmid": a.get("pmid", ""), "doi": a.get("doi", "")})
            elif isinstance(a, str):
                results.append({"pmid": a})
            else:
                results.append({"title": getattr(a, "title", ""), "pmid": getattr(a, "pmid", ""), "doi": getattr(a, "doi", "")})
        return {
            "source": "pubmed",
            "query": query,
            "count": len(results),
            "results": results,
        }

    # --- Local API handlers: arXiv ---

    def _local_arxiv_search(self, params: dict) -> dict:
        from jarvis_core.sources import ArxivClient
        client = ArxivClient()
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        papers = client.search(query, max_results=max_results)
        return {
            "source": "arxiv",
            "query": query,
            "count": len(papers),
            "results": [p.to_dict() if hasattr(p, "to_dict") else {"title": p.title} for p in papers],
        }

    # --- Local API handlers: Crossref ---

    def _local_crossref_search(self, params: dict) -> dict:
        from jarvis_core.sources import CrossrefClient
        client = CrossrefClient()
        query = params.get("query", "")
        rows = params.get("rows", 5)
        works = client.search(query, rows=rows)
        return {
            "source": "crossref",
            "query": query,
            "count": len(works),
            "results": [{"title": w.title, "doi": w.doi} for w in works],
        }

    def _local_crossref_doi(self, params: dict) -> dict:
        doi = params.get("doi", "")
        url = f"https://api.crossref.org/works/{doi}"
        headers = {"User-Agent": "JARVIS Research OS/2.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        item = resp.json().get("message", {})
        title_list = item.get("title", [])
        return {
            "source": "crossref",
            "doi": doi,
            "title": title_list[0] if title_list else "",
            "authors": [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in item.get("author", [])
            ],
            "year": item.get("published-print", item.get("published-online", {})).get("date-parts", [[None]])[0][0],
            "journal": item.get("container-title", [""])[0],
        }

    # --- Local API handlers: OpenAlex ---

    def _local_openalex_search(self, params: dict) -> dict:
        from jarvis_core.sources import OpenAlexClient
        client = OpenAlexClient()
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        works = client.search(query, max_results=max_results)
        return {
            "source": "openalex",
            "query": query,
            "count": len(works),
            "results": [{"title": w.title, "doi": getattr(w, "doi", "")} for w in works],
        }

    def _local_openalex_work(self, params: dict) -> dict:
        work_id = params.get("id", "")
        url = f"https://api.openalex.org/works/{work_id}"
        headers = {"User-Agent": "JARVIS Research OS/2.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        w = resp.json()
        return {
            "source": "openalex",
            "id": w.get("id", ""),
            "doi": w.get("doi", ""),
            "title": w.get("title", ""),
            "year": w.get("publication_year"),
            "cited_by_count": w.get("cited_by_count", 0),
            "abstract": w.get("abstract", ""),
        }

    # --- Local API handlers: Semantic Scholar ---

    def _local_s2_search(self, params: dict) -> dict:
        query = params.get("query", "")
        limit = min(params.get("limit", 5), 100)
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        resp = requests.get(
            url,
            params={"query": query, "limit": limit, "fields": "title,authors,year,abstract,externalIds,citationCount"},
            headers={"User-Agent": "JARVIS Research OS/2.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        papers = data.get("data", [])
        results = []
        for p in papers:
            ext = p.get("externalIds", {}) or {}
            results.append({
                "paperId": p.get("paperId", ""),
                "title": p.get("title", ""),
                "year": p.get("year"),
                "citationCount": p.get("citationCount", 0),
                "doi": ext.get("DOI", ""),
                "authors": [a.get("name", "") for a in (p.get("authors") or [])],
                "abstract": (p.get("abstract") or "")[:300],
            })
        return {
            "source": "semantic_scholar",
            "query": query,
            "total": data.get("total", 0),
            "count": len(results),
            "results": results,
        }

    def _local_s2_paper(self, params: dict) -> dict:
        paper_id = params.get("paper_id", "")
        fields = "title,authors,year,abstract,externalIds,citationCount,referenceCount,venue"
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        resp = requests.get(
            url,
            params={"fields": fields},
            headers={"User-Agent": "JARVIS Research OS/2.0"},
            timeout=15,
        )
        resp.raise_for_status()
        p = resp.json()
        ext = p.get("externalIds", {}) or {}
        return {
            "source": "semantic_scholar",
            "paperId": p.get("paperId", ""),
            "title": p.get("title", ""),
            "year": p.get("year"),
            "doi": ext.get("DOI", ""),
            "citationCount": p.get("citationCount", 0),
            "referenceCount": p.get("referenceCount", 0),
            "venue": p.get("venue", ""),
            "authors": [a.get("name", "") for a in (p.get("authors") or [])],
            "abstract": p.get("abstract") or "",
        }

    def _local_s2_citations(self, params: dict) -> dict:
        paper_id = params.get("paper_id", "")
        limit = min(params.get("limit", 10), 100)
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
        resp = requests.get(
            url,
            params={"fields": "title,authors,year,externalIds", "limit": limit},
            headers={"User-Agent": "JARVIS Research OS/2.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        results = []
        for item in data:
            cp = item.get("citingPaper", {})
            ext = cp.get("externalIds", {}) or {}
            results.append({
                "paperId": cp.get("paperId", ""),
                "title": cp.get("title", ""),
                "year": cp.get("year"),
                "doi": ext.get("DOI", ""),
            })
        return {
            "source": "semantic_scholar",
            "paper_id": paper_id,
            "count": len(results),
            "citations": results,
        }

    def _local_s2_references(self, params: dict) -> dict:
        paper_id = params.get("paper_id", "")
        limit = min(params.get("limit", 10), 100)
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references"
        resp = requests.get(
            url,
            params={"fields": "title,authors,year,externalIds", "limit": limit},
            headers={"User-Agent": "JARVIS Research OS/2.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        results = []
        for item in data:
            cp = item.get("citedPaper", {})
            ext = cp.get("externalIds", {}) or {}
            results.append({
                "paperId": cp.get("paperId", ""),
                "title": cp.get("title", ""),
                "year": cp.get("year"),
                "doi": ext.get("DOI", ""),
            })
        return {
            "source": "semantic_scholar",
            "paper_id": paper_id,
            "count": len(results),
            "references": results,
        }

    # --- Async methods (kept for compatibility) ---

    async def discover_tools(self, server_name: str) -> list[MCPTool]:
        server = self._servers.get(server_name)
        if not server:
            return []
        return server.tools

    async def invoke_tool(self, tool_name: str, params: dict) -> MCPToolResult:
        return self.invoke_tool_sync(tool_name, params)

    def list_all_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for server in self._servers.values():
            for tool in server.tools:
                tools.append({
                    "server": server.name,
                    "tool": tool.name,
                    "description": tool.description,
                    "enabled": tool.enabled,
                    "required_params": tool.required_params,
                })
        return tools

    def list_servers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": server.name,
                "server_url": server.server_url,
                "server_type": server.server_type,
                "status": server.status.value,
                "tool_count": len(server.tools),
            }
            for server in self._servers.values()
        ]

    def _find_tool(self, tool_name: str) -> tuple[MCPServer | None, MCPTool | None]:
        for server in self._servers.values():
            for tool in server.tools:
                if tool.name == tool_name:
                    return server, tool
        return None, None

    def _allow_request(self, server: MCPServer) -> bool:
        if not server.requests_per_minute:
            return True
        now = time.time()
        window_start = now - 60
        timestamps = [t for t in self._rate_log[server.name] if t >= window_start]
        self._rate_log[server.name] = timestamps
        if len(timestamps) >= server.requests_per_minute:
            return False
        timestamps.append(now)
        self._rate_log[server.name] = timestamps
        return True
'''

target.write_text(code, encoding="utf-8")
print(f"Created: {target} ({target.stat().st_size} bytes)")
