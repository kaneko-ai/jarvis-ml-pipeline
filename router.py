# router.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

import yaml

from llm import LLMClient, Message
from agents import ThesisAgent, ESEditAgent, MiscAgent, AgentResult


@dataclass
class RoutePlan:
    task_type: str            # "thesis" / "es_edit" / "misc" など
    importance: str           # "low" / "medium" / "high"
    use_sampling: bool        # 多案生成するかどうか


class Router:
    def __init__(self, llm: LLMClient, config_path: str = "config.yaml") -> None:
        self.llm = llm
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.agents = {
            "thesis": ThesisAgent(),
            "es_edit": ESEditAgent(),
            "misc": MiscAgent(),
        }

    def plan_route(self, user_task: str) -> RoutePlan:
        """
        LLMに「これはどの種類のタスクで、重要度はどれくらいか」を判定させる。
        結果はJSONで返してもらい、RoutePlanに変換。
        """
        system_prompt = (
            "あなたはタスク分類アシスタントです。"
            "ユーザーの依頼文を読んで、次の3つをJSONで答えてください。\n"
            "task_type: 'thesis' | 'paper_survey' | 'es_edit' | 'misc'\n"
            "importance: 'low' | 'medium' | 'high'\n"
            "理由は不要です。JSONオブジェクトのみを出力してください。"
        )
        raw = self.llm.chat(
            [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_task),
            ]
        )

        import json

        try:
            obj = json.loads(raw)
            task_type = obj.get("task_type", "misc")
            importance = obj.get("importance", "high")
        except json.JSONDecodeError:
            task_type = "misc"
            importance = "high"

        use_sampling = (
            importance in self.config.get("router", {})
            .get("use_sampling_for_importance", ["high"])
        )

        if task_type not in self.agents:
            task_type = "misc"

        return RoutePlan(
            task_type=task_type,
            importance=importance,
            use_sampling=use_sampling,
        )

    def run(self, user_task: str) -> AgentResult:
        plan = self.plan_route(user_task)
        agent = self.agents[plan.task_type]

        if plan.use_sampling:
            n = self.config.get("sampling", {}).get("num_candidates", 3)
            candidates = agent.run_sampling(self.llm, user_task, n)
            best = self.select_best_candidate(candidates, user_task)
            self._log(user_task, plan, candidates, best)
            return best
        else:
            result = agent.run_single(self.llm, user_task)
            self._log(user_task, plan, [result], result)
            return result

    def select_best_candidate(
        self, candidates: List[AgentResult], user_task: str
    ) -> AgentResult:
        """
        単純には score 最大を選ぶ。
        将来的には、別の Evaluator エージェントに
        「どの案が最も良いか」を判断させる拡張も可能。
        """
        if not candidates:
            raise ValueError("No candidates")

        # 現状は単純にスコア最大
        best = max(candidates, key=lambda c: c.score)
        return best

    def _log(
        self,
        user_task: str,
        plan: RoutePlan,
        candidates: List[AgentResult],
        best: AgentResult,
    ) -> None:
        import os
        import json
        from datetime import datetime

        log_dir = self.config.get("logging", {}).get("save_dir", "logs")
        os.makedirs(log_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(log_dir, f"log_{ts}.json")

        data: Dict[str, Any] = {
            "task": user_task,
            "plan": {
                "task_type": plan.task_type,
                "importance": plan.importance,
                "use_sampling": plan.use_sampling,
            },
            "candidates": [
                {
                    "thought": c.thought,
                    "answer": c.answer,
                    "score": c.score,
                    "meta": c.meta,
                }
                for c in candidates
            ],
            "best": {
                "thought": best.thought,
                "answer": best.answer,
                "score": best.score,
                "meta": best.meta,
            },
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
