from __future__ import annotations

from pathlib import Path

import pytest

from async_test_utils import run_async
from jarvis_core.browser.agents.pdf_download import PDFDownloadAgent


class _Resp:
    def __init__(self, status_code: int, *, content: bytes = b"", text: str = "", payload=None):
        self.status_code = status_code
        self.content = content
        self.text = text
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_download_success_and_failure(monkeypatch, tmp_path: Path) -> None:
    agent = PDFDownloadAgent()
    out_ok = tmp_path / "ok" / "paper.pdf"
    out_ng = tmp_path / "ng" / "paper.pdf"

    calls = {"n": 0}

    def fake_get(url: str, timeout: int = 0):  # noqa: ARG001
        calls["n"] += 1
        if "success" in url:
            return _Resp(200, content=b"%PDF-1.7")
        return _Resp(404, content=b"")

    monkeypatch.setattr("jarvis_core.browser.agents.pdf_download.requests.get", fake_get)

    ok = run_async(agent.download("https://example.com/success.pdf", out_ok))
    ng = run_async(agent.download("https://example.com/fail.pdf", out_ng))

    assert ok is True
    assert out_ok.read_bytes() == b"%PDF-1.7"
    assert ng is False
    assert not out_ng.exists()
    assert calls["n"] == 2


def test_find_pdf_link_prefers_unpaywall_for_doi(monkeypatch) -> None:
    agent = PDFDownloadAgent()

    async def fake_fetch(doi: str) -> str:  # noqa: ARG001
        return "https://oa.example/paper.pdf"

    monkeypatch.setattr(agent, "_fetch_unpaywall_link", fake_fetch)

    link = run_async(agent.find_pdf_link("10.1000/xyz.1"))
    assert link == "https://oa.example/paper.pdf"


def test_find_pdf_link_fallback_to_html_and_helpers(monkeypatch) -> None:
    agent = PDFDownloadAgent()

    async def fake_fetch_none(doi: str):  # noqa: ARG001
        return None

    monkeypatch.setattr(agent, "_fetch_unpaywall_link", fake_fetch_none)

    html = '<html><a href="/assets/final.pdf">pdf</a></html>'
    monkeypatch.setattr(
        "jarvis_core.browser.agents.pdf_download.requests.get",
        lambda url, timeout=0: _Resp(200, text=html),
    )

    link = run_async(agent.find_pdf_link("10.5555/abc"))
    assert link and link.endswith("/assets/final.pdf")

    assert PDFDownloadAgent._extract_pdf_link("https://host/path", '<a href="doc.PDF">x</a>') == (
        "https://host/doc.PDF"
    )
    assert PDFDownloadAgent._extract_pdf_link("https://host/path", "<a href='x.txt'>x</a>") is None
    assert PDFDownloadAgent._looks_like_doi("10.1000/182")
    assert not PDFDownloadAgent._looks_like_doi("https://doi.org/10.1000/182")
    assert PDFDownloadAgent.default_output_path("a.pdf").as_posix().endswith("downloads/a.pdf")


def test_fetch_unpaywall_link_and_non200(monkeypatch) -> None:
    agent = PDFDownloadAgent(unpaywall_email="x@example.com")

    responses = [
        _Resp(200, payload={"best_oa_location": {"url_for_pdf": "https://oa/pdf"}}),
        _Resp(500, payload={}),
    ]

    def fake_get(url: str, timeout: int = 0):  # noqa: ARG001
        return responses.pop(0)

    monkeypatch.setattr("jarvis_core.browser.agents.pdf_download.requests.get", fake_get)

    ok = run_async(agent._fetch_unpaywall_link("10.1/ok"))
    ng = run_async(agent._fetch_unpaywall_link("10.1/ng"))
    assert ok == "https://oa/pdf"
    assert ng is None
