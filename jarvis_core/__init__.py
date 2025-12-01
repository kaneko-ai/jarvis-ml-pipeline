"""Jarvis Core package exports."""

from .task import Task, TaskCategory, TaskPriority, TaskStatus
from .registry import AgentRegistry

__all__ = [
    "run_jarvis",
    "Task",
    "TaskCategory",
    "TaskPriority",
    "TaskStatus",
    "AgentRegistry",
    "LLMClient",
    "Router",
]


def run_jarvis(task: str) -> str:
    """
    High-level wrapper that orchestrates a task through the router.

    Imports heavy dependencies lazily so that lightweight modules (e.g.,
    task modeling) can be used without requiring LLM dependencies.
    """

    from .llm import LLMClient  # Local import to avoid optional dependency at package import time
    from .router import Router

    llm = LLMClient(model="gemini-2.0-flash")
    router = Router(llm)
    result = router.run(task)
    return result.answer


def __getattr__(name: str):
    if name == "LLMClient":
        from .llm import LLMClient

        return LLMClient
    if name == "Router":
        from .router import Router

        return Router
    if name == "AgentRegistry":
        from .registry import AgentRegistry

        return AgentRegistry
    raise AttributeError(name)
