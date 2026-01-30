"""Core implementation for the browser subagent."""

from __future__ import annotations

import base64
import importlib
import importlib.util
import time
from dataclasses import dataclass
from typing import Any

from jarvis_core.browser.recording import BrowserRecorder, generate_session_id
from jarvis_core.browser.schema import (
    BrowserAction,
    BrowserActionResult,
    BrowserState,
    SecurityPolicy,
)
from jarvis_core.browser.security import BrowserSecurityManager


@dataclass
class _PlaywrightSession:
    playwright: Any
    browser: Any
    page: Any


class BrowserSubagent:
    """Playwright-based browser subagent."""

    def __init__(
        self,
        security_policy: SecurityPolicy | None = None,
        headless: bool = True,
    ) -> None:
        self.security_manager = BrowserSecurityManager(policy=security_policy or SecurityPolicy())
        self.headless = headless
        self.session: _PlaywrightSession | None = None
        self.state = BrowserState()
        self.recorder: BrowserRecorder | None = None

    async def initialize(self) -> None:
        async_playwright = self._load_async_playwright()
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=self.headless)
        page = await browser.new_page()
        self.session = _PlaywrightSession(playwright=playwright, browser=browser, page=page)

    async def navigate(self, url: str) -> BrowserActionResult:
        start = time.perf_counter()
        if not self.security_manager.check_url(url):
            return self._result(
                BrowserAction.NAVIGATE,
                False,
                error=f"URL not allowed by security policy: {url}",
                duration_ms=self._elapsed_ms(start),
            )
        await self._ensure_initialized()
        await self.session.page.goto(url)
        await self._refresh_state()
        await self._capture_recording_frame()
        return self._result(
            BrowserAction.NAVIGATE, True, data={"url": url}, duration_ms=self._elapsed_ms(start)
        )

    async def click(self, selector: str) -> BrowserActionResult:
        start = time.perf_counter()
        await self._ensure_initialized()
        await self.session.page.click(selector)
        await self._refresh_state()
        await self._capture_recording_frame()
        return self._result(
            BrowserAction.CLICK,
            True,
            data={"selector": selector},
            duration_ms=self._elapsed_ms(start),
        )

    async def type_text(self, selector: str, text: str) -> BrowserActionResult:
        start = time.perf_counter()
        await self._ensure_initialized()
        await self.session.page.fill(selector, text)
        await self._refresh_state()
        await self._capture_recording_frame()
        return self._result(
            BrowserAction.TYPE,
            True,
            data={"selector": selector, "text": text},
            duration_ms=self._elapsed_ms(start),
        )

    async def screenshot(self, full_page: bool = False) -> BrowserActionResult:
        start = time.perf_counter()
        await self._ensure_initialized()
        image_bytes = await self.session.page.screenshot(full_page=full_page)
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        await self._capture_recording_frame(image_bytes)
        return self._result(
            BrowserAction.SCREENSHOT,
            True,
            data={"full_page": full_page},
            screenshot=encoded,
            duration_ms=self._elapsed_ms(start),
        )

    async def extract_text(self, selector: str) -> BrowserActionResult:
        start = time.perf_counter()
        await self._ensure_initialized()
        element = await self.session.page.query_selector(selector)
        text = None
        if element is not None:
            text = await element.inner_text()
        await self._refresh_state()
        return self._result(
            BrowserAction.EXTRACT_TEXT,
            True,
            data={"selector": selector, "text": text},
            duration_ms=self._elapsed_ms(start),
        )

    async def close(self) -> None:
        if self.session is None:
            return
        await self.session.page.close()
        await self.session.browser.close()
        await self.session.playwright.stop()
        self.session = None

    def start_recording(self) -> None:
        if self.recorder is None:
            self.recorder = BrowserRecorder(session_id=generate_session_id())
        self.recorder.start_recording()

    def stop_recording(self) -> str:
        if self.recorder is None:
            return str(BrowserRecorder(session_id=generate_session_id()).stop_recording())
        recording_path = self.recorder.stop_recording()
        return str(recording_path)

    async def _ensure_initialized(self) -> None:
        if self.session is None:
            raise RuntimeError("BrowserSubagent is not initialized. Call initialize() first.")

    async def _refresh_state(self) -> None:
        if self.session is None:
            return
        self.state.current_url = self.session.page.url
        self.state.title = await self.session.page.title()

    async def _capture_recording_frame(self, image_bytes: bytes | None = None) -> None:
        if self.recorder is None or not self.recorder.active:
            return
        if image_bytes is None:
            image_bytes = await self.session.page.screenshot(full_page=False)
        self.recorder.capture_frame(image_bytes)

    def _result(
        self,
        action: BrowserAction,
        success: bool,
        data: Any = None,
        error: str | None = None,
        screenshot: str | None = None,
        duration_ms: float | None = None,
    ) -> BrowserActionResult:
        return BrowserActionResult(
            action=action,
            success=success,
            data=data,
            error=error,
            screenshot=screenshot,
            duration_ms=duration_ms,
        )

    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return (time.perf_counter() - start) * 1000

    @staticmethod
    def _load_async_playwright():
        if importlib.util.find_spec("playwright.async_api") is None:
            raise RuntimeError("playwright is not installed. Install jarvis-research-os[browser].")
        module = importlib.import_module("playwright.async_api")
        return module.async_playwright