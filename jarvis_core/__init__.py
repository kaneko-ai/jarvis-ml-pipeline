"""Jarvis Core package exports."""

from .registry import AgentRegistry
from .task import Task, TaskCategory, TaskPriority, TaskStatus

__all__ = [
    "run_jarvis",
    "Task",
    "TaskCategory",
    "TaskPriority",
    "TaskStatus",
    "AgentRegistry",
    "LLMClient",
    "Router",
    "timeline",
    "clinical_readiness",
    "lab_optimizer",
]


def run_jarvis(goal: str, category: str = "generic") -> str:
    """
    High-level wrapper that orchestrates a task through the unified pipeline.

    This function ALWAYS produces telemetry logs at logs/runs/{run_id}/.

    Args:
        goal: The user's goal or request as a string.
        category: Task category. One of: "paper_survey", "thesis",
            "job_hunting", "generic". Defaults to "generic".

    Returns:
        The final answer as a string.
    """
    from .app import run_task

    result = run_task(
        task_dict={"goal": goal, "category": category},
        run_config_dict=None,
    )

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

    if name == "active_learning":
        import importlib

        return importlib.import_module(".active_learning", __name__)

    if name in ("timeline", "clinical_readiness", "lab_optimizer"):
        import importlib

        return importlib.import_module(f".experimental.{name}", __name__)

    try:
        import importlib

        return importlib.import_module(f".experimental.{name}", __name__)
    except ModuleNotFoundError as e:
        if e.name == f"{__name__}.experimental.{name}":
            raise AttributeError(name) from e
        raise

    raise AttributeError(name)
