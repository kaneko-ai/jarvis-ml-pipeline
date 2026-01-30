"""Research agent implementation."""

from __future__ import annotations

import asyncio

from jarvis_core import run_jarvis
from jarvis_core.orchestrator.artifact_store import ArtifactStore
from jarvis_core.orchestrator.multi_agent import MultiAgentOrchestrator
from jarvis_core.orchestrator.schema import AgentTask


class ResearchAgent:
    """Agent that runs literature research tasks."""

    async def execute(self, task: AgentTask, orchestrator: MultiAgentOrchestrator) -> None:
        agent_id = orchestrator.find_agent_id(task.task_id) or task.task_id
        store = ArtifactStore()

        task_plan = """# Task Plan

1. Clarify the research goal.
2. Identify key keywords and sources.
3. Gather and summarize evidence.
"""
        implementation_plan = """# Implementation Plan

- Execute the research plan in stages.
- Capture findings and citations.
- Summarize outputs for downstream use.
"""

        result = await asyncio.to_thread(run_jarvis, task.description)
        walkthrough = """# Walkthrough

## Goal
{goal}

## Result
{result}
""".format(
            goal=task.description, result=result
        )

        for filename, content in (
            ("task_plan.md", task_plan),
            ("implementation_plan.md", implementation_plan),
            ("walkthrough.md", walkthrough),
        ):
            path = store.save(agent_id, filename, content)
            await orchestrator.record_artifact(agent_id, path)