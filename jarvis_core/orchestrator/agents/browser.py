"""Browser agent implementation."""

from __future__ import annotations

import asyncio
import base64
import re

from jarvis_core.browser.subagent import BrowserSubagent
from jarvis_core.orchestrator.multi_agent import AgentTask, MultiAgentOrchestrator


class BrowserAgent:
    """Agent that performs browser-based tasks."""

    def __init__(self, agent_id: str = "browser_agent") -> None:
        self.agent_id = agent_id
        self.agent_type = "browser"

    async def execute(self, task: AgentTask, orchestrator: MultiAgentOrchestrator) -> None:
        """Execute a browser task and store artifacts."""
        url = _extract_url(task.payload.get("url") or task.description)
        if not url:
            message = "No URL provided in task description."
            path = orchestrator.artifact_store.save(self.agent_id, "extracted_text.txt", message)
            await orchestrator.notify_artifact_created(self.agent_id, path)
            return

        subagent = BrowserSubagent(headless=True)
        try:
            await subagent.initialize()
            subagent.start_recording()
            await subagent.navigate(url)
            screenshot = await subagent.screenshot(full_page=True)
            text_result = await subagent.extract_text("body")
            recording_path = subagent.stop_recording()
        except Exception as exc:
            error_text = f"Browser task failed: {exc}"
            path = orchestrator.artifact_store.save(self.agent_id, "extracted_text.txt", error_text)
            await orchestrator.notify_artifact_created(self.agent_id, path)
            return
        finally:
            await asyncio.sleep(0)
            await subagent.close()

        if screenshot.screenshot:
            image_bytes = base64.b64decode(screenshot.screenshot.encode("utf-8"))
            path = orchestrator.artifact_store.save(self.agent_id, "screenshot.png", image_bytes)
            await orchestrator.notify_artifact_created(self.agent_id, path)

        extracted_text = text_result.data.get("text") if text_result.data else None
        text_content = extracted_text or ""
        text_path = orchestrator.artifact_store.save(self.agent_id, "extracted_text.txt", text_content)
        await orchestrator.notify_artifact_created(self.agent_id, text_path)

        if recording_path:
            recording_text = f"Recording stored at: {recording_path}"
            recording_artifact = orchestrator.artifact_store.save(
                self.agent_id,
                "recording.txt",
                recording_text,
            )
            await orchestrator.notify_artifact_created(self.agent_id, recording_artifact)


def _extract_url(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"https?://\\S+", text)
    return match.group(0) if match else None
