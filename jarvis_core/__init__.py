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


def run_jarvis(goal: str, category: str = "generic") -> str:
    """
    High-level wrapper that orchestrates a task through the ExecutionEngine.

    This function creates a Task from the provided goal and category,
    executes it via the ExecutionEngine, and returns the final answer.

    Args:
        goal: The user's goal or request as a string.
        category: Task category. One of: "paper_survey", "thesis",
            "job_hunting", "generic". Defaults to "generic".

    Returns:
        The final answer as a string.

    Imports heavy dependencies lazily so that lightweight modules (e.g.,
    task modeling) can be used without requiring LLM dependencies.
    """
    import uuid

    from .executor import ExecutionEngine
    from .llm import LLMClient
    from .planner import Planner
    from .router import Router
    from .evidence import EvidenceStore

    # Validate and convert category
    try:
        task_category = TaskCategory(category)
    except ValueError:
        task_category = TaskCategory.GENERIC

    llm = LLMClient(model="gemini-2.0-flash")
    router = Router(llm)
    planner = Planner()
    evidence_store = EvidenceStore()
    engine = ExecutionEngine(
        planner=planner,
        router=router,
        evidence_store=evidence_store,
    )

    root_task = Task(
        task_id=str(uuid.uuid4()),
        title=goal,
        category=task_category,
        user_goal=goal,
        inputs={"query": goal},
    )

    return engine.run_and_get_answer(root_task)


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
