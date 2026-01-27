"""arXiv specific browser agent."""

from __future__ import annotations

from typing import Any

from jarvis_core.browser.subagent import BrowserSubagent


class ArxivBrowserAgent(BrowserSubagent):
    """Browser automation tailored to arXiv."""

    BASE_URL = "https://arxiv.org/"
    SEARCH_URL = "https://arxiv.org/search/"
    SEARCH_INPUT = "input#query"
    RESULT_ITEM = "li.arxiv-result"
    RESULT_TITLE = "p.title"
    RESULT_ID = "p.list-title"
    ABSTRACT_SECTION = "blockquote.abstract"

    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        await self.navigate(f"{self.SEARCH_URL}?query={query}&searchtype=all")
        await self._ensure_initialized()
        results = []
        items = await self.session.page.query_selector_all(self.RESULT_ITEM)
        for item in items[:max_results]:
            title_el = await item.query_selector(self.RESULT_TITLE)
            id_el = await item.query_selector(self.RESULT_ID)
            title = await title_el.inner_text() if title_el else None
            raw_id = await id_el.inner_text() if id_el else ""
            arxiv_id = raw_id.replace("arXiv:", "").strip()
            link_el = await item.query_selector("p.list-title a")
            link = await link_el.get_attribute("href") if link_el else None
            results.append({"title": title, "arxiv_id": arxiv_id, "link": link})
        return results

    async def get_abstract(self, arxiv_id: str) -> str:
        await self.navigate(f"{self.BASE_URL}abs/{arxiv_id}")
        await self._ensure_initialized()
        abstract_el = await self.session.page.query_selector(self.ABSTRACT_SECTION)
        if abstract_el is None:
            return ""
        return await abstract_el.inner_text()

    async def get_pdf_url(self, arxiv_id: str) -> str:
        return f"{self.BASE_URL}pdf/{arxiv_id}.pdf"
