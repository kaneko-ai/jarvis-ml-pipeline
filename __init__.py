"""Root package entrypoints for Jarvis pipeline."""

from jarvis_core.task import Task, TaskCategory, TaskPriority, TaskStatus

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "run_jarvis",
    "Task",
    "TaskCategory",
    "TaskPriority",
    "TaskStatus",
    "LLMClient",
    "Router",
    "Planner",
    "ExecutionEngine",
]


def run_jarvis(task: str) -> str:
    from jarvis_core.llm import LLMClient
    from jarvis_core.router import Router

    llm = LLMClient(model="gemini-2.0-flash")
    router = Router(llm)
    result = router.run(task)
    return result.answer


def __getattr__(name: str):
    if name == "LLMClient":
        from jarvis_core.llm import LLMClient

        return LLMClient
    if name == "Router":
        from jarvis_core.router import Router

        return Router
    if name == "Planner":
        from jarvis_core.planner import Planner

        return Planner
    if name == "ExecutionEngine":
        from jarvis_core.executor import ExecutionEngine

        return ExecutionEngine
    raise AttributeError(name)
