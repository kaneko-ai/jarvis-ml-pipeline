"""Browser agent implementation."""

from __future__ import annotations

import base64
import re

from jarvis_core.browser.subagent import BrowserSubagent
from jarvis_core.orchestrator.artifact_store import ArtifactStore
from jarvis_core.orchestrator.multi_agent import MultiAgentOrchestrator
from jarvis_core.orchestrator.schema import AgentTask


class BrowserAgent:
    """Agent that performs browser-based tasks."""

    URL_PATTERN = re.compile(r"https?://\S+")

    async def execute(self, task: AgentTask, orchestrator: MultiAgentOrchestrator) -> None:
        agent_id = orchestrator.find_agent_id(task.task_id) or task.task_id
        store = ArtifactStore()
        url = self._extract_url(task.description)

        if not url:
            message = f"No URL found in task description: {task.description}"
            path = store.save(agent_id, "extracted_text.txt", message)
            await orchestrator.record_artifact(agent_id, path)
            return

        subagent = BrowserSubagent(headless=True)
        subagent.start_recording()
        await subagent.initialize()
        try:
            await subagent.navigate(url)
            screenshot_result = await subagent.screenshot(full_page=True)
            text_result = await subagent.extract_text("body")
        finally:
            subagent.stop_recording()
            await subagent.close()

        if screenshot_result.screenshot:
            image_bytes = base64.b64decode(screenshot_result.screenshot)
            screenshot_path = store.save(agent_id, "screenshot.png", image_bytes)
            await orchestrator.record_artifact(agent_id, screenshot_path)

        extracted_text = text_result.data.get("text") if text_result.data else None
        text_content = extracted_text or ""
        text_path = store.save(agent_id, "extracted_text.txt", text_content)
        await orchestrator.record_artifact(agent_id, text_path)

        if subagent.recorder:
            for index, frame_path in enumerate(subagent.recorder.list_frames(), start=1):
                frame_bytes = frame_path.read_bytes()
                filename = f"recording_frame_{index:04d}.png"
                saved_path = store.save(agent_id, filename, frame_bytes)
                await orchestrator.record_artifact(agent_id, saved_path)

    @classmethod
    def _extract_url(cls, text: str) -> str | None:
        match = cls.URL_PATTERN.search(text)
        if not match:
            return None
        return match.group(0)
