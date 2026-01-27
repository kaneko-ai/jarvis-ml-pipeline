"""Shared API state for orchestrator and other services."""

from __future__ import annotations

from jarvis_core.orchestrator import MultiAgentOrchestrator
from jarvis_core.orchestrator.agents import BrowserAgent, ResearchAgent


_orchestrator = MultiAgentOrchestrator()
_orchestrator.register_agent(ResearchAgent())
_orchestrator.register_agent(BrowserAgent())


def get_orchestrator() -> MultiAgentOrchestrator:
    """Return the shared orchestrator instance."""
    return _orchestrator
