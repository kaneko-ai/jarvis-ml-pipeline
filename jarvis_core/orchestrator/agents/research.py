"""Research agent implementation."""

from __future__ import annotations

import asyncio

from jarvis_core import run_jarvis
from jarvis_core.orchestrator.multi_agent import AgentTask, MultiAgentOrchestrator


class ResearchAgent:
    """Agent that runs literature research tasks."""

    def __init__(self, agent_id: str = "research_agent") -> None:
        self.agent_id = agent_id
        self.agent_type = "research"

    async def execute(self, task: AgentTask, orchestrator: MultiAgentOrchestrator) -> None:
        """Execute a research task and generate artifacts."""
        goal = task.payload.get("goal") or task.description
        prompt = (
            "Generate a structured task plan, implementation plan, and walkthrough for: "
            f"{goal}"
        )
        try:
            output = await asyncio.to_thread(run_jarvis, prompt, "generic")
        except Exception as exc:
            output = f"Run failed: {exc}"

        task_plan = f"# Task Plan\n\n{output}\n"
        implementation_plan = f"# Implementation Plan\n\n{output}\n"
        walkthrough = f"# Walkthrough\n\n{output}\n"

        artifacts = {
            "task_plan.md": task_plan,
            "implementation_plan.md": implementation_plan,
            "walkthrough.md": walkthrough,
        }
        for filename, content in artifacts.items():
            path = orchestrator.artifact_store.save(self.agent_id, filename, content)
            await orchestrator.notify_artifact_created(self.agent_id, path)
