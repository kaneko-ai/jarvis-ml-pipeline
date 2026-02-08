"""CLI tests for MCP and Skills commands (TD-011/TD-013)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis_cli import cmd_mcp, cmd_skills


def _write_mcp_config(path: Path) -> None:
    payload = {
        "mcpServers": {
            "mock": {
                "serverUrl": "https://mcp.example",
                "type": "http",
                "tools": [
                    {
                        "name": "search",
                        "description": "Search tool",
                        "parameters": {"query": "string"},
                        "required_params": ["query"],
                        "enabled": True,
                    }
                ],
            }
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_cmd_mcp_list_json(tmp_path, capsys):
    config_path = tmp_path / "mcp.json"
    _write_mcp_config(config_path)

    args = SimpleNamespace(
        config=str(config_path),
        json=True,
        mcp_command="list",
        server_name=None,
        tool_name=None,
        params=None,
    )
    cmd_mcp(args)

    payload = json.loads(capsys.readouterr().out)
    assert payload["servers"][0]["name"] == "mock"
    assert payload["tools"][0]["tool"] == "search"


def test_cmd_mcp_invoke_json(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "mcp.json"
    _write_mcp_config(config_path)

    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"result": "ok"}

    def fake_request(method: str, url: str, headers=None, json=None, timeout=30):
        assert method == "POST"
        assert url.endswith("/invoke")
        assert json["tool"] == "search"
        return _FakeResponse()

    monkeypatch.setattr("requests.request", fake_request)

    args = SimpleNamespace(
        config=str(config_path),
        json=True,
        mcp_command="invoke",
        tool_name="search",
        params='{"query":"cd73"}',
        server_name=None,
    )
    cmd_mcp(args)

    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is True
    assert payload["data"] == {"result": "ok"}


def test_cmd_skills_list_and_show(tmp_path, monkeypatch, capsys):
    skill_dir = tmp_path / ".agent" / "skills" / "demo"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: Demo Skill\n"
        "description: Demo description\n"
        "triggers:\n"
        "  - demo\n"
        "---\n\n"
        "Run demo steps.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    list_args = SimpleNamespace(json=True, skills_command="list", skill_name=None, query=None)
    cmd_skills(list_args)
    list_payload = json.loads(capsys.readouterr().out)
    assert list_payload[0]["name"] == "Demo Skill"

    show_args = SimpleNamespace(
        json=True, skills_command="show", skill_name="Demo Skill", query=None
    )
    cmd_skills(show_args)
    show_payload = json.loads(capsys.readouterr().out)
    assert show_payload["skill"] == "Demo Skill"
    assert "Run demo steps." in show_payload["context"]


def test_cmd_skills_show_missing_exits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = SimpleNamespace(json=False, skills_command="show", skill_name="missing", query=None)
    with pytest.raises(SystemExit) as exc:
        cmd_skills(args)
    assert exc.value.code == 1
