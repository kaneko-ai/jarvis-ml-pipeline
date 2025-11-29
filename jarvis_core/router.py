from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .agents import ThesisAgent, ESEditAgent, MiscAgent, AgentResult
from .llm import LLMClient


@dataclass
class RoutePlan:
    task_type: str
    agent_name: str
    meta: Dict[str, Any]


class Router:
    """
    タスク内容から担当エージェントを選び、実行するだけのシンプルなルーター。
    ログ保存など余計な処理は一旦すべて削っている。
    """

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

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

        if any(k in t for k in thesis_keywords):
            return "thesis"
        if any(k in t for k in es_keywords):
            return "es"

        return "misc"

    def plan_route(self, task: str) -> RoutePlan:
        task_type = self._detect_task_type(task)

        if task_type == "thesis":
            agent_name = "thesis"
        elif task_type == "es":
            agent_name = "es_edit"
        else:
            agent_name = "misc"

        return RoutePlan(
            task_type=task_type,
            agent_name=agent_name,
            meta={"raw_task": task[:200]},
        )

    # ---------- 実行 ----------

    def run(self, task: str) -> AgentResult:
        plan = self.plan_route(task)

        if plan.agent_name == "thesis":
            agent = ThesisAgent()
        elif plan.agent_name == "es_edit":
            agent = ESEditAgent()
        else:
            agent = MiscAgent()

        result = agent.run_single(self.llm, task)
        return result
