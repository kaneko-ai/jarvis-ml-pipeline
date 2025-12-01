"""Minimal example to run a literature task through the AgentRegistry and Router."""
from __future__ import annotations

from pathlib import Path

from jarvis_core.registry import AgentRegistry
from jarvis_core.router import Router
from jarvis_core.task import Task, TaskCategory


class DummyLLM:
    """Minimal stub with the `chat` method used by agents."""

    def chat(self, messages):  # noqa: D401, ANN001
        return "dummy response"


def main() -> None:
    config_path = Path(__file__).resolve().parent.parent / "configs" / "agents.example.yaml"
    registry = AgentRegistry.from_file(config_path)
    router = Router(llm=DummyLLM(), registry=registry)

    task = Task(
        id="demo-literature-1",
        category=TaskCategory.PAPER_SURVEY,
        goal="Summarize recent papers about CRISPR quality control",
        inputs={"query": "CRISPR quality control"},
    )

    result = router.run(task)
    print(f"[{task.category.value}] {task.goal}")
    print(f"Agent answer: {result.answer}")


if __name__ == "__main__":
    main()
