from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)

from .agents import (
    AgentResult,
    ESEditAgent,
    JobAssistantAgent,
    MiscAgent,
    PaperFetcherAgent,
    ThesisAgent,
)
from .llm import LLMClient
from .registry import AgentRegistry
from .task import Task, TaskCategory


@dataclass
class RoutePlan:
    task_type: str
    agent_name: str
    meta: dict[str, Any]


class Router:
    """
    タスク内容から担当エージェントを選び、実行するだけのシンプルなルーター。
    ログ保存など余計な処理は一旦すべて削っている。
    """

    def __init__(self, llm: LLMClient, registry: AgentRegistry | None = None) -> None:
        self.llm = llm
        if registry:
            self.registry = registry
        else:
            default_path = Path(__file__).resolve().parent.parent / "configs" / "agents.yaml"
            self.registry = AgentRegistry.from_file(default_path)

    # ---------- ルーティングロジック ----------

    def _detect_task_type(self, text: str) -> str:
        t = text

        thesis_keywords = [
            "修士論文",
            "修論",
            "考察",
            "背景",
            "結果の文章",
            "図の説明",
            "Figure legend",
            "Figure レジェンド",
        ]
        es_keywords = [
            "ES",
            "エントリーシート",
            "志望動機",
            "自己PR",
            "自己ＰＲ",
            "ガクチカ",
            "就活",
            "インターン",
        ]
        paper_keywords = ["文献", "サーベイ", "論文", "paper"]

        if any(k in t for k in thesis_keywords):
            return TaskCategory.THESIS.value
        if any(k in t for k in es_keywords):
            return TaskCategory.JOB_HUNTING.value
        if any(k in t for k in paper_keywords):
            return TaskCategory.PAPER_SURVEY.value

        return TaskCategory.GENERIC.value

    def plan_route(self, task: str) -> RoutePlan:
        task_type = self._detect_task_type(task)
        agent_name: str | None = None

        if task_type == TaskCategory.JOB_HUNTING.value and self.registry.get_agent("es_edit"):
            agent_name = "es_edit"

        if agent_name is None:
            default = self.registry.get_default_agent_for_category(task_type)
            if default:
                agent_name = default.name

        if agent_name is None:
            agent_name = "misc"

        return RoutePlan(
            task_type=task_type,
            agent_name=agent_name,
            meta={"raw_task": task[:200]},
        )

    def _select_agent_for_task(self, task: Task):
        inputs = task.inputs or {}
        agent_hint = inputs.get("agent_hint") if isinstance(inputs, dict) else None
        if agent_hint:
            try:
                return self.registry.create_agent_instance(agent_hint)
            except KeyError as e:
                logger.debug(f"Agent hint '{agent_hint}' not found in registry: {e}")

        default = self.registry.get_default_agent_for_category(task.category.value)
        if default:
            return self.registry.create_agent_instance(default.name)

        return MiscAgent()

    def _render_task_text(self, task: Task) -> str:
        context = ""
        if isinstance(task.inputs, dict):
            query = task.inputs.get("query")
            ctx = task.inputs.get("context")
            parts = [task.goal]
            if query:
                parts.append(f"Query: {query}")
            if ctx:
                parts.append(f"Context: {ctx}")
            context = "\n".join(parts)
        return context or task.goal

    def run_task(self, task: Task) -> AgentResult:
        agent = self._select_agent_for_task(task)
        task_text = self._render_task_text(task)
        return agent.run_single(self.llm, task_text)

    # ---------- 実行 ----------

    def run(self, task: str | Task) -> AgentResult:
        if isinstance(task, Task):
            return self.run_task(task)

        plan = self.plan_route(task)

        if plan.agent_name == "thesis":
            agent = ThesisAgent()
        elif plan.agent_name == "es_edit":
            agent = ESEditAgent()
        elif plan.agent_name == "paper_fetcher":
            agent = PaperFetcherAgent()
        elif plan.agent_name == "job_assistant":
            agent = JobAssistantAgent()
        else:
            agent = MiscAgent()

        result = agent.run_single(self.llm, task)
        return result