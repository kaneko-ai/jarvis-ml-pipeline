"""TD-012 tests for browser security policy and runtime behavior."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from jarvis_core.browser.schema import SecurityPolicy
from jarvis_core.browser.security import BrowserSecurityManager
from jarvis_core.browser.subagent import BrowserSubagent


def test_security_policy_allows_listed_url():
    manager = BrowserSecurityManager(policy=SecurityPolicy(url_allow_list=["example.com"]))
    assert manager.check_url("https://example.com/page") is True


def test_security_policy_blocks_unlisted_url():
    manager = BrowserSecurityManager(policy=SecurityPolicy(url_allow_list=["allowed.com"]))
    assert manager.check_url("https://blocked.com/page") is False


def test_browser_subagent_uses_headless_setting(monkeypatch):
    launch_calls: list[bool] = []

    class _FakePage:
        async def close(self) -> None:
            return None

    class _FakeBrowser:
        async def new_page(self):
            return _FakePage()

        async def close(self) -> None:
            return None

    class _FakeChromium:
        async def launch(self, headless: bool):
            launch_calls.append(headless)
            return _FakeBrowser()

    class _FakePlaywright:
        def __init__(self) -> None:
            self.chromium = _FakeChromium()

        async def stop(self) -> None:
            return None

    class _FakeContext:
        async def start(self):
            return _FakePlaywright()

    def fake_async_playwright():
        return _FakeContext()

    monkeypatch.setattr(
        BrowserSubagent, "_load_async_playwright", staticmethod(lambda: fake_async_playwright)
    )

    agent = BrowserSubagent(headless=False)
    asyncio.run(agent.initialize())
    assert launch_calls == [False]
    asyncio.run(agent.close())


def test_browser_subagent_timeout_returns_error(monkeypatch):
    class _SlowPage:
        async def goto(self, url: str) -> None:
            await asyncio.sleep(0.05)

    agent = BrowserSubagent(
        security_policy=SecurityPolicy(url_allow_list=["example.com"]),
        action_timeout_s=0.01,
    )
    agent.session = SimpleNamespace(page=_SlowPage())

    async def no_init() -> None:
        return None

    monkeypatch.setattr(agent, "_ensure_initialized", no_init)
    result = asyncio.run(agent.navigate("https://example.com"))
    assert result.success is False
    assert "timed out" in (result.error or "").lower()
