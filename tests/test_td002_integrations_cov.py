from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from jarvis_core.integrations import additional as add_mod
from jarvis_core.integrations import external as ext_mod


class _FakeResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> bool:
        return False


def _raise(exc: Exception) -> None:
    raise exc


def test_external_integrations_success_and_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    # Slack
    slack = ext_mod.SlackNotifier(ext_mod.SlackConfig(webhook_url="https://slack", channel="#c"))
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(b"{}", status=200),
    )
    assert slack.send_message("hello")
    assert not slack.send_paper_alert([])
    assert slack.send_paper_alert([{"title": "A", "authors": "B", "journal": "J", "pmid": "1"}])

    # Notion
    notion = ext_mod.NotionSync(ext_mod.NotionConfig(api_key="k", database_id="db"))
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(b'{"id":"page-1"}', status=200),
    )
    assert notion._make_request("pages", method="GET") == {"id": "page-1"}
    assert notion.add_paper(
        {"title": "T", "pmid": "1", "authors": "A", "journal": "J", "year": 2024}
    )
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _raise(RuntimeError("net")),
    )
    assert notion._make_request("pages") is None

    # ORCID
    orcid = ext_mod.ORCIDClient()
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(
            b'{"name":{"given-names":{"value":"Jane"},"family-name":{"value":"Doe"}}}'
        ),
    )
    assert orcid.get_author("0000-0000")["name"] == "Jane"
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _raise(RuntimeError("err")),
    )
    assert orcid.get_author("0000-0000") is None

    # arXiv
    arxiv = ext_mod.ArXivClient()
    xml = (
        "<feed><entry><title>Paper X</title><id>http://arxiv.org/abs/1234.5678</id>"
        "<summary>Summary text</summary></entry></feed>"
    )
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _url, timeout=10: _FakeResponse(xml.encode("utf-8")),
    )
    papers = arxiv.search("ml", max_results=2)
    assert papers and papers[0]["arxiv_id"] == "1234.5678"
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _url, timeout=10: _raise(RuntimeError("err")),
    )
    assert arxiv.search("ml") == []

    # Semantic Scholar
    ss = ext_mod.SemanticScholarClient(api_key="k")
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(
            b'{"data":[{"paperId":"p1","title":"T","authors":[{"name":"A"}],"year":2024,"citationCount":2}]}'
        ),
    )
    result = ss.search("query", limit=1)
    assert result and result[0]["paper_id"] == "p1"
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _url, timeout=10: _FakeResponse(b'{"paperId":"p1","title":"T"}'),
    )
    assert ss.get_paper("p1")["paperId"] == "p1"
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _raise(RuntimeError("err")),
    )
    assert ss.search("q") == []
    assert ss.get_paper("p1") is None

    # GitHub issue creator
    gh = ext_mod.GitHubIssueCreator(token="t", owner="o", repo="r")
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(b'{"html_url":"https://github.com/o/r/issues/1"}'),
    )
    assert gh.create_issue("x", "y", ["a"]).endswith("/1")
    assert gh.create_paper_issue({"title": "P", "authors": "A"}) is not None
    monkeypatch.setattr(
        ext_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _raise(RuntimeError("err")),
    )
    assert gh.create_issue("x", "y") is None

    assert isinstance(ext_mod.get_slack_notifier("https://slack"), ext_mod.SlackNotifier)
    assert isinstance(ext_mod.get_arxiv_client(), ext_mod.ArXivClient)
    assert isinstance(ext_mod.get_semantic_scholar_client(), ext_mod.SemanticScholarClient)


def test_additional_integrations_success_and_error_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Zotero
    zot = add_mod.ZoteroClient(add_mod.ZoteroConfig(api_key="k", user_id="u"))
    monkeypatch.setattr(
        add_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(b'[{"key":"x"}]', status=200),
    )
    assert zot.get_items(limit=1) == [{"key": "x"}]
    assert zot.search("q") == [{"key": "x"}]
    assert zot.add_item({"title": "T", "authors": "A,B", "journal": "J", "year": 2024, "pmid": "1"})
    monkeypatch.setattr(
        add_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _raise(RuntimeError("err")),
    )
    assert zot.get_items() == []
    assert zot.search("q") == []
    assert not zot.add_item({"title": "T"})

    # Google Drive
    drive = add_mod.GoogleDriveExporter(
        add_mod.GoogleDriveConfig(access_token="token", folder_id="f1")
    )
    monkeypatch.setattr(
        add_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(b'{"files":[{"id":"1"}]}', status=200),
    )
    assert drive.list_files(limit=1) == [{"id": "1"}]
    assert drive.export_json("x.json", {"a": 1}) == "file_x.json"
    assert drive.export_papers([{"title": "T"}], filename="papers.json") == "file_papers.json"

    # Discord
    discord = add_mod.DiscordBot(add_mod.DiscordConfig(bot_token="t", channel_id="c"))
    monkeypatch.setattr(
        add_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _FakeResponse(b"{}", status=201),
    )
    assert discord.send_message("hello")
    assert discord.send_paper_alert([{"title": "A", "authors": "B", "journal": "J"}])
    monkeypatch.setattr(
        add_mod.urllib.request,
        "urlopen",
        lambda _req, timeout=10: _raise(RuntimeError("err")),
    )
    assert not discord.send_message("hello")

    # Obsidian
    vault = tmp_path / "vault"
    vault.mkdir()
    obs = add_mod.ObsidianExporter(vault_path=str(vault))
    md = obs.paper_to_markdown({"title": "P", "authors": "A", "journal": "J", "tags": ["x"]})
    assert "Created by [[JARVIS Research OS]]" in md
    filename = obs.export_paper({"title": "Paper:One", "authors": "A", "journal": "J"})
    assert filename.endswith(".md")
    assert (vault / filename).exists()
    all_files = obs.export_all([{"title": "T1"}, {"title": "T2"}])
    assert len(all_files) == 2

    # Dashboard
    manager = add_mod.DashboardManager()
    widget = add_mod.Widget("w1", "stats", "Stats", {"x": 0, "y": 0, "w": 1, "h": 1}, {})
    manager.add_widget(widget)
    manager.update_position("w1", {"x": 1, "y": 1, "w": 2, "h": 2})
    manager.save_layout("main")
    assert manager.load_layout("main")
    assert not manager.load_layout("missing")
    manager.remove_widget("w1")
    assert manager.widgets == []
    assert len(manager.get_default_layout()) == 5

    # Split view
    split = add_mod.SplitViewManager()
    split.set_layout("vertical")
    split.set_pane_content("left", {"content": "x"})
    assert "display: flex" in split.generate_css()
    split.set_layout("horizontal")
    assert "flex-direction: column" in split.generate_css()
    split.set_layout("quad")
    assert "grid-template-columns" in split.generate_css()
    split.set_layout("unknown")
    assert split.current_layout == "quad"

    # Full screen
    fs = add_mod.FullScreenManager()
    state1 = fs.toggle("viewer")
    state2 = fs.toggle("viewer")
    assert state1["action"] == "enter"
    assert state2["action"] == "exit"
    assert "toggleFullscreen" in fs.generate_js()

    # Annotation manager
    ann_mgr = add_mod.AnnotationManager()
    ann = add_mod.Annotation(
        id="",
        paper_id="p1",
        text="note",
        highlight_color="yellow",
        page=1,
        position={"x": 0, "y": 0, "width": 1, "height": 1},
    )
    ann_id = ann_mgr.add_annotation("p1", ann)
    assert ann_id.startswith("ann_")
    assert ann_mgr.get_annotations("p1")
    assert ann_mgr.delete_annotation("p1", ann_id)
    exported = ann_mgr.export_annotations("p1")
    assert exported["paper_id"] == "p1"

    # 3D config
    cfg = add_mod.ThreeDAnimationConfig()
    conf = cfg.generate_config()
    assert conf["enabled"] is True
    assert "Three.js" in cfg.generate_js_snippet()

    # Factory functions
    assert isinstance(add_mod.get_zotero_client("k", "u"), add_mod.ZoteroClient)
    assert isinstance(add_mod.get_google_drive_exporter("t"), add_mod.GoogleDriveExporter)
    assert isinstance(add_mod.get_discord_bot("t", "c"), add_mod.DiscordBot)
    assert isinstance(add_mod.get_obsidian_exporter(), add_mod.ObsidianExporter)
    assert isinstance(add_mod.get_dashboard_manager(), add_mod.DashboardManager)
    assert isinstance(add_mod.get_annotation_manager(), add_mod.AnnotationManager)
