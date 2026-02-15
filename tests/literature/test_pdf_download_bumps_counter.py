from __future__ import annotations

from pathlib import Path

from async_test_utils import run_async
from jarvis_core.browser.agents.pdf_download import PDFDownloadAgent
from jarvis_core.literature.paper_counter import PaperCounterStore


class _Resp:
    def __init__(self, status_code: int, *, content: bytes = b"", text: str = "") -> None:
        self.status_code = status_code
        self.content = content
        self.text = text

    def json(self):
        return {}


def test_pdf_download_bumps_counter(monkeypatch, tmp_path: Path) -> None:
    counter = PaperCounterStore(tmp_path / "papers.json")
    counter.init_if_missing()
    agent = PDFDownloadAgent(run_id="runA", counter=counter)

    html = '<html><a href="/paper.pdf">pdf</a></html>'

    def fake_get(url: str, timeout: int = 0):  # noqa: ARG001
        if url.endswith(".pdf"):
            return _Resp(200, content=b"%PDF-1.7")
        return _Resp(200, text=html)

    monkeypatch.setattr("jarvis_core.browser.agents.pdf_download.requests.get", fake_get)

    link = run_async(agent.find_pdf_link("https://example.com/landing"))
    assert link and link.endswith("/paper.pdf")
    ok = run_async(agent.download(link, tmp_path / "paper.pdf"))
    assert ok is True

    snap = counter.snapshot()
    assert snap["totals"]["discovered"] == 1
    assert snap["totals"]["downloaded"] == 1
    assert snap["by_run"]["runA"]["discovered"] == 1
    assert snap["by_run"]["runA"]["downloaded"] == 1
