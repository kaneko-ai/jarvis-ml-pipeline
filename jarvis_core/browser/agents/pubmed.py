"""PubMed specific browser agent."""

from __future__ import annotations

from typing import Any

from jarvis_core.browser.schema import BrowserActionResult
from jarvis_core.browser.subagent import BrowserSubagent


class PubMedBrowserAgent(BrowserSubagent):
    """Browser automation tailored to PubMed."""

    BASE_URL = "https://pubmed.ncbi.nlm.nih.gov/"
    SEARCH_INPUT = "input#id_term"
    SEARCH_FORM = "form#search-form"
    RESULT_ITEMS = "article.full-docsum"
    RESULT_TITLE = "a.docsum-title"
    RESULT_PMID = "span.docsum-pmid"
    ABSTRACT_SECTION = "div.abstract-content"
    PDF_LINK = "a.link-item"  # often includes PDF or publisher link

    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        await self.navigate(f"{self.BASE_URL}?term={query}")
        await self._ensure_initialized()
        results = []
        items = await self.session.page.query_selector_all(self.RESULT_ITEMS)
        for item in items[:max_results]:
            title_el = await item.query_selector(self.RESULT_TITLE)
            pmid_el = await item.query_selector(self.RESULT_PMID)
            title = await title_el.inner_text() if title_el else None
            pmid = await pmid_el.inner_text() if pmid_el else None
            link = await title_el.get_attribute("href") if title_el else None
            results.append({"title": title, "pmid": pmid, "link": link})
        return results

    async def get_abstract(self, pmid: str) -> str:
        await self.navigate(f"{self.BASE_URL}{pmid}/")
        await self._ensure_initialized()
        abstract_el = await self.session.page.query_selector(self.ABSTRACT_SECTION)
        if abstract_el is None:
            return ""
        return await abstract_el.inner_text()

    async def download_pdf_link(self, pmid: str) -> str | None:
        await self.navigate(f"{self.BASE_URL}{pmid}/")
        await self._ensure_initialized()
        links = await self.session.page.query_selector_all(self.PDF_LINK)
        for link in links:
            href = await link.get_attribute("href")
            text = (await link.inner_text()).lower() if link else ""
            if href and "pdf" in text:
                return href
        return None

    async def navigate(self, url: str) -> BrowserActionResult:
        return await super().navigate(url)
