"""Coverage tests for jarvis_core.orchestrator.agents.browser."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from async_test_utils import sync_async_test
from jarvis_core.orchestrator.agents.browser import BrowserAgent


class TestExtractUrl:
    def test_with_url(self) -> None:
        url = BrowserAgent._extract_url("Go to https://example.com/page and extract")
        assert url == "https://example.com/page"

    def test_without_url(self) -> None:
        assert BrowserAgent._extract_url("No url here") is None

    def test_http_url(self) -> None:
        url = BrowserAgent._extract_url("Visit http://foo.bar/baz")
        assert url == "http://foo.bar/baz"


class TestBrowserAgentExecute:
    def _mock_task(self, description: str = "Get https://example.com"):
        task = MagicMock()
        task.task_id = "task-1"
        task.description = description
        return task

    def _mock_orchestrator(self):
        orchestrator = MagicMock()
        orchestrator.find_agent_id.return_value = "agent-1"
        orchestrator.record_artifact = AsyncMock()
        return orchestrator

    @sync_async_test
    async def test_no_url(self) -> None:
        agent = BrowserAgent()
        task = self._mock_task("No links here")
        orch = self._mock_orchestrator()

        with patch("jarvis_core.orchestrator.agents.browser.ArtifactStore") as MockStore:
            MockStore.return_value.save.return_value = "/tmp/artifact"
            await agent.execute(task, orch)

        MockStore.return_value.save.assert_called_once()

    @sync_async_test
    async def test_with_url_success(self) -> None:
        agent = BrowserAgent()
        task = self._mock_task("Get https://example.com")
        orch = self._mock_orchestrator()

        mock_subagent = MagicMock()
        mock_subagent.initialize = AsyncMock()
        mock_subagent.navigate = AsyncMock()
        mock_subagent.close = AsyncMock()
        mock_subagent.start_recording = MagicMock()
        mock_subagent.stop_recording = MagicMock()

        screenshot_result = MagicMock()
        screenshot_result.screenshot = "aGVsbG8="  # base64 "hello"
        mock_subagent.screenshot = AsyncMock(return_value=screenshot_result)

        text_result = MagicMock()
        text_result.data = {"text": "Page content"}
        mock_subagent.extract_text = AsyncMock(return_value=text_result)

        mock_subagent.recorder = None

        with patch(
            "jarvis_core.orchestrator.agents.browser.BrowserSubagent", return_value=mock_subagent
        ):
            with patch("jarvis_core.orchestrator.agents.browser.ArtifactStore") as MockStore:
                MockStore.return_value.save.return_value = "/tmp/file"
                await agent.execute(task, orch)

        mock_subagent.navigate.assert_awaited_once()
        mock_subagent.screenshot.assert_awaited_once()

    @sync_async_test
    async def test_with_url_no_screenshot(self) -> None:
        agent = BrowserAgent()
        task = self._mock_task("Get https://example.com")
        orch = self._mock_orchestrator()

        mock_subagent = MagicMock()
        mock_subagent.initialize = AsyncMock()
        mock_subagent.navigate = AsyncMock()
        mock_subagent.close = AsyncMock()
        mock_subagent.start_recording = MagicMock()
        mock_subagent.stop_recording = MagicMock()

        screenshot_result = MagicMock()
        screenshot_result.screenshot = None
        mock_subagent.screenshot = AsyncMock(return_value=screenshot_result)

        text_result = MagicMock()
        text_result.data = None
        mock_subagent.extract_text = AsyncMock(return_value=text_result)

        mock_subagent.recorder = None

        with patch(
            "jarvis_core.orchestrator.agents.browser.BrowserSubagent", return_value=mock_subagent
        ):
            with patch("jarvis_core.orchestrator.agents.browser.ArtifactStore") as MockStore:
                MockStore.return_value.save.return_value = "/tmp/file"
                await agent.execute(task, orch)

    @sync_async_test
    async def test_with_recorder_frames(self) -> None:
        agent = BrowserAgent()
        task = self._mock_task("Get https://example.com")
        orch = self._mock_orchestrator()

        mock_subagent = MagicMock()
        mock_subagent.initialize = AsyncMock()
        mock_subagent.navigate = AsyncMock()
        mock_subagent.close = AsyncMock()
        mock_subagent.start_recording = MagicMock()
        mock_subagent.stop_recording = MagicMock()

        screenshot_result = MagicMock()
        screenshot_result.screenshot = None
        mock_subagent.screenshot = AsyncMock(return_value=screenshot_result)

        text_result = MagicMock()
        text_result.data = {"text": "content"}
        mock_subagent.extract_text = AsyncMock(return_value=text_result)

        frame_path = MagicMock()
        frame_path.read_bytes.return_value = b"frame_data"
        mock_subagent.recorder = MagicMock()
        mock_subagent.recorder.list_frames.return_value = [frame_path, frame_path]

        with patch(
            "jarvis_core.orchestrator.agents.browser.BrowserSubagent", return_value=mock_subagent
        ):
            with patch("jarvis_core.orchestrator.agents.browser.ArtifactStore") as MockStore:
                MockStore.return_value.save.return_value = "/tmp/file"
                await agent.execute(task, orch)

        # 2 frames saved
        assert MockStore.return_value.save.call_count >= 3  # text + 2 frames
