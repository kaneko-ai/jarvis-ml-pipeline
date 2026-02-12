from types import SimpleNamespace

import pytest

from async_test_utils import run_async
from jarvis_core.browser.schema import SecurityPolicy
from jarvis_core.browser.security import BrowserSecurityManager
from jarvis_core.browser.subagent import BrowserSubagent


class _FakeElement:
    async def inner_text(self):
        return "Hello world"


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
        if selector == "#missing":
            return None
        return _FakeElement()


@pytest.mark.integration
def test_browser_url_allow_deny():
    policy = SecurityPolicy(url_allow_list=["allowed.com"], url_deny_list=["blocked.com"])
    manager = BrowserSecurityManager(policy=policy)

    assert manager.check_url("https://allowed.com/page") is True
    assert manager.check_url("https://blocked.com/page") is False


@pytest.mark.integration
def test_browser_navigation_and_screenshot(monkeypatch):
    agent = BrowserSubagent(security_policy=SecurityPolicy(url_allow_list=["example.com"]))
    agent.session = SimpleNamespace(page=_FakePage())

    async def no_init():
        return None

    monkeypatch.setattr(agent, "_ensure_initialized", no_init)

    nav_result = run_async(agent.navigate("https://example.com"))
    shot_result = run_async(agent.screenshot(full_page=True))

    assert nav_result.success is True
    assert nav_result.data["url"] == "https://example.com"
    assert shot_result.screenshot is not None


@pytest.mark.integration
def test_browser_text_extraction(monkeypatch):
    agent = BrowserSubagent(security_policy=SecurityPolicy(url_allow_list=["example.com"]))
    agent.session = SimpleNamespace(page=_FakePage())

    async def no_init():
        return None

    monkeypatch.setattr(agent, "_ensure_initialized", no_init)

    result = run_async(agent.extract_text("#content"))
    assert result.data["text"] == "Hello world"
