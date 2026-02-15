"""PDF download agent."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from jarvis_core.literature.paper_counter import PaperCounterStore


@dataclass
class PDFDownloadAgent:
    """Agent that locates and downloads PDFs."""

    unpaywall_email: str = "jarvis@kaneko-ai.dev"
    run_id: str | None = None
    counter: PaperCounterStore | None = None

    def _bump_counter(self, field: str) -> bool:
        if self.counter is None:
            return False
        run_id = str(self.run_id or "").strip()
        if not run_id:
            return False
        try:
            self.counter.bump(run_id=run_id, field=field, delta=1)
            return True
        except Exception:
            return False

    async def download(self, url: str, output_path: Path) -> bool:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = await asyncio.to_thread(requests.get, url, timeout=30)
        if response.status_code != 200:
            return False
        output_path.write_bytes(response.content)
        self._bump_counter("downloaded")
        return True

    async def find_pdf_link(self, page_url: str) -> str | None:
        if self._looks_like_doi(page_url):
            oa_link = await self._fetch_unpaywall_link(page_url)
            if oa_link:
                self._bump_counter("discovered")
                return oa_link
        response = await asyncio.to_thread(requests.get, page_url, timeout=30)
        if response.status_code != 200:
            return None
        resolved = self._extract_pdf_link(page_url, response.text)
        if resolved:
            self._bump_counter("discovered")
        return resolved

    async def _fetch_unpaywall_link(self, doi: str) -> str | None:
        api_url = f"https://api.unpaywall.org/v2/{doi}?email={self.unpaywall_email}"
        response = await asyncio.to_thread(requests.get, api_url, timeout=30)
        if response.status_code != 200:
            return None
        payload: dict[str, Any] = response.json()
        location = payload.get("best_oa_location") or {}
        return location.get("url_for_pdf")

    @staticmethod
    def default_output_path(filename: str) -> Path:
        return Path("downloads") / filename

    @staticmethod
    def _extract_pdf_link(base_url: str, html: str) -> str | None:
        for match in re.findall(r'href=["\'](.*?)["\']', html, flags=re.IGNORECASE):
            if match.lower().endswith(".pdf"):
                return urljoin(base_url, match)
        return None

    @staticmethod
    def _looks_like_doi(text: str) -> bool:
        parsed = urlparse(text)
        if parsed.scheme in {"http", "https"}:
            return False
        return text.startswith("10.")
