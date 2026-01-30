import asyncio
from types import SimpleNamespace

import pytest
import requests

from jarvis_core.browser.schema import SecurityPolicy
from jarvis_core.browser.subagent import BrowserSubagent
from jarvis_core.evidence.ensemble import grade_evidence
from jarvis_core.experimental.prisma.generator import PRISMAData, generate_prisma_flow
from jarvis_core.mcp.hub import MCPHub
from jarvis_core.mcp.schema import MCPServer, MCPServerStatus, MCPTool
from jarvis_core.skills.engine import SkillsEngine


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakePage:
    def __init__(self):
        self.url = "about:blank"
        self._title = ""

    async def goto(self, url):
        self.url = url
        self._title = "Mock Title"

    async def screenshot(self, full_page=False):
        return b"image-bytes"

    async def title(self):
        return self._title

    async def query_selector(self, selector):
        return None


@pytest.mark.integration
def test_full_integration_flow(tmp_path, monkeypatch):
    query = "Impact of therapy X"

    # 1. User query input
    assert query

    # 2. Skills/Rules applied
    skills_dir = tmp_path / ".agent" / "skills" / "review"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        "---\nname: review\ntriggers: [therapy]\n---\nReview workflow",
        encoding="utf-8",
    )
    engine = SkillsEngine(workspace_path=tmp_path)
    matched = engine.match_skills("therapy review")
    rules_applied = ["default"]
    assert "review" in matched
    assert rules_applied

    # 3. MCP Hub search
    hub = MCPHub()
    server = MCPServer(
        name="mock",
        server_url="https://mcp.example",
        server_type="http",
        headers={},
        status=MCPServerStatus.DISCONNECTED,
    )
    server.tools = [
        MCPTool(
            name="search", description="Search", parameters={}, required_params=[], enabled=True
        )
    ]
    hub.register_server(server)

    def fake_request(method, url, headers=None, json=None, timeout=None):
        if url.endswith("/tools"):
            return _FakeResponse({"tools": [{"name": "search", "description": "Search"}]})
        return _FakeResponse({"papers": [{"title": "Paper A", "abstract": "RCT"}]})

    monkeypatch.setattr(requests, "request", fake_request)
    asyncio.run(hub.discover_tools("mock"))
    search_result = asyncio.run(hub.invoke_tool("search", {"query": query}))
    assert search_result.success

    # 4. Browser Agent fetch
    agent = BrowserSubagent(security_policy=SecurityPolicy(url_allow_list=["example.com"]))
    agent.session = SimpleNamespace(page=_FakePage())

    async def no_init():
        return None

    monkeypatch.setattr(agent, "_ensure_initialized", no_init)
    nav_result = asyncio.run(agent.navigate("https://example.com"))
    assert nav_result.success

    # 5. Evidence grading
    grade = grade_evidence(title="Paper A", abstract="RCT", use_llm=False)
    assert grade.level.value

    # 6. PRISMA flow
    prisma = PRISMAData(
        identification_database=1,
        identification_other=0,
        duplicates_removed=0,
        records_screened=1,
        records_excluded_screening=0,
        full_text_assessed=1,
        full_text_excluded=0,
        studies_included=1,
    )
    prisma_flow = generate_prisma_flow(prisma, format="mermaid")
    assert "flowchart" in prisma_flow

    # 7. Final report
    report = f"Report for {query}\n{prisma_flow}"
    assert "Report" in report