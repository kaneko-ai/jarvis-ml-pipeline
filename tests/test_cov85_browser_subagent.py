"""Coverage tests for jarvis_core.browser.subagent."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from async_test_utils import sync_async_test
from jarvis_core.browser.schema import (
    BrowserAction,
    BrowserActionResult,
    BrowserState,
    SecurityPolicy,
)
from jarvis_core.browser.subagent import BrowserSubagent, _PlaywrightSession


class TestBrowserSubagentInit:
    def test_defaults(self) -> None:
        agent = BrowserSubagent()
        assert agent.headless is True
        assert agent.action_timeout_s == 30.0
        assert agent.session is None
        assert agent.recorder is None

    def test_custom(self) -> None:
        policy = SecurityPolicy()
        agent = BrowserSubagent(security_policy=policy, headless=False, action_timeout_s=10.0)
        assert agent.headless is False
        assert agent.action_timeout_s == 10.0


class TestNavigate:
    @sync_async_test
    async def test_url_blocked(self) -> None:
        agent = BrowserSubagent()
        agent.security_manager = MagicMock()
        agent.security_manager.check_url.return_value = False
        result = await agent.navigate("http://evil.com")
        assert result.success is False
        assert "not allowed" in result.error

    @sync_async_test
    async def test_success(self) -> None:
        agent = BrowserSubagent()
        agent.security_manager = MagicMock()
        agent.security_manager.check_url.return_value = True
        mock_page = AsyncMock()
        mock_page.url = "http://example.com"
        mock_page.title.return_value = "Example"
        mock_page.screenshot.return_value = b"image"
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.navigate("http://example.com")
        assert result.success is True
        assert result.data["url"] == "http://example.com"

    @sync_async_test
    async def test_timeout(self) -> None:
        agent = BrowserSubagent(action_timeout_s=0.001)
        agent.security_manager = MagicMock()
        agent.security_manager.check_url.return_value = True
        mock_page = AsyncMock()
        mock_page.goto.side_effect = asyncio.TimeoutError()
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.navigate("http://example.com")
        assert result.success is False
        assert "timed out" in result.error


class TestClick:
    @sync_async_test
    async def test_success(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.url = "http://example.com"
        mock_page.title.return_value = "Example"
        mock_page.screenshot.return_value = b"img"
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.click("#btn")
        assert result.success is True

    @sync_async_test
    async def test_timeout(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.click.side_effect = asyncio.TimeoutError()
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.click("#btn")
        assert result.success is False


class TestTypeText:
    @sync_async_test
    async def test_success(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.url = "http://example.com"
        mock_page.title.return_value = "Example"
        mock_page.screenshot.return_value = b"img"
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.type_text("#input", "hello")
        assert result.success is True

    @sync_async_test
    async def test_timeout(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.fill.side_effect = asyncio.TimeoutError()
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.type_text("#input", "hello")
        assert result.success is False


class TestScreenshot:
    @sync_async_test
    async def test_success(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.screenshot.return_value = b"image_bytes"
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.screenshot()
        assert result.success is True
        assert result.screenshot == "aW1hZ2VfYnl0ZXM="

    @sync_async_test
    async def test_timeout(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.screenshot.side_effect = asyncio.TimeoutError()
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.screenshot()
        assert result.success is False


class TestExtractText:
    @sync_async_test
    async def test_element_found(self) -> None:
        agent = BrowserSubagent()
        mock_element = AsyncMock()
        mock_element.inner_text.return_value = "Hello World"
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = mock_element
        mock_page.url = "http://example.com"
        mock_page.title.return_value = "Example"
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.extract_text("body")
        assert result.success is True
        assert result.data["text"] == "Hello World"

    @sync_async_test
    async def test_element_not_found(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = None
        mock_page.url = "http://example.com"
        mock_page.title.return_value = "Example"
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.extract_text("#nonexistent")
        assert result.success is True
        assert result.data["text"] is None

    @sync_async_test
    async def test_timeout(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_page.query_selector.side_effect = asyncio.TimeoutError()
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        result = await agent.extract_text("body")
        assert result.success is False


class TestCloseAndRecording:
    @sync_async_test
    async def test_close_no_session(self) -> None:
        agent = BrowserSubagent()
        await agent.close()  # Should not raise

    @sync_async_test
    async def test_close_with_session(self) -> None:
        agent = BrowserSubagent()
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()
        agent.session = _PlaywrightSession(
            playwright=mock_playwright, browser=mock_browser, page=mock_page
        )
        await agent.close()
        assert agent.session is None
        mock_page.close.assert_awaited_once()

    @sync_async_test
    async def test_start_recording(self) -> None:
        agent = BrowserSubagent()
        agent.start_recording()
        assert agent.recorder is not None
        assert agent.recorder.active is True
        assert agent.recorder.session_id.startswith("browser_")

    @sync_async_test
    async def test_stop_recording_no_recorder(self) -> None:
        agent = BrowserSubagent()
        result = agent.stop_recording()
        assert "logs" in result
        assert "browser_recordings" in result

    @sync_async_test
    async def test_stop_recording_with_recorder(self) -> None:
        agent = BrowserSubagent()
        agent.start_recording()
        session_id = agent.recorder.session_id if agent.recorder else ""
        result = agent.stop_recording()
        assert "logs" in result
        assert "browser_recordings" in result
        assert session_id in result
        assert agent.recorder is not None
        assert agent.recorder.active is False


class TestEnsureInitialized:
    @sync_async_test
    async def test_raises_when_not_initialized(self) -> None:
        agent = BrowserSubagent()
        with pytest.raises(RuntimeError, match="not initialized"):
            await agent._ensure_initialized()

    @sync_async_test
    async def test_passes_when_initialized(self) -> None:
        agent = BrowserSubagent()
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=MagicMock()
        )
        await agent._ensure_initialized()  # Should not raise


class TestCaptureRecordingFrame:
    @sync_async_test
    async def test_no_recorder(self) -> None:
        agent = BrowserSubagent()
        await agent._capture_recording_frame()  # Should not raise

    @sync_async_test
    async def test_recorder_not_active(self) -> None:
        agent = BrowserSubagent()
        agent.recorder = MagicMock()
        agent.recorder.active = False
        await agent._capture_recording_frame()  # Should not raise

    @sync_async_test
    async def test_recorder_active_captures(self) -> None:
        agent = BrowserSubagent()
        agent.recorder = MagicMock()
        agent.recorder.active = True
        mock_page = AsyncMock()
        mock_page.screenshot.return_value = b"frame"
        agent.session = _PlaywrightSession(
            playwright=MagicMock(), browser=MagicMock(), page=mock_page
        )
        await agent._capture_recording_frame()
        agent.recorder.capture_frame.assert_called_once()


class TestHelpers:
    def test_result(self) -> None:
        agent = BrowserSubagent()
        result = agent._result(BrowserAction.NAVIGATE, True, data={"url": "http://example.com"})
        assert result.action == BrowserAction.NAVIGATE
        assert result.success is True

    def test_elapsed_ms(self) -> None:
        start = time.perf_counter()
        elapsed = BrowserSubagent._elapsed_ms(start)
        assert elapsed >= 0

    def test_timeout_message(self) -> None:
        agent = BrowserSubagent(action_timeout_s=5.0)
        assert "5.0" in agent._timeout_message()

    def test_load_async_playwright_missing(self) -> None:
        with patch("importlib.util.find_spec", return_value=None):
            with pytest.raises(RuntimeError, match="playwright"):
                BrowserSubagent._load_async_playwright()
