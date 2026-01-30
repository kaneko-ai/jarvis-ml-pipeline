"""
JARVIS Action Planner

Phase 4: 行動計画
- Read（読む）
- Build（作る）
- Ignore（捨てる）

人間とAIの役割分担を明示。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """行動タイプ."""

    READ = "read"  # 読む
    BUILD = "build"  # 作る
    IGNORE = "ignore"  # 捨てる


class Executor(Enum):
    """実行者."""

    HUMAN = "human"
    AI = "ai"
    BOTH = "both"


@dataclass
class ActionItem:
    """行動アイテム."""

    action_type: ActionType
    target: str  # 対象（論文/コード/タスク）
    reason: str  # 理由
    executor: Executor  # 誰がやるか
    executor_reason: str  # なぜその人がやるか
    priority: int = 3  # 1-5
    estimated_effort: str = ""  # 見積もり時間

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "action": self.action_type.value,
            "target": self.target,
            "reason": self.reason,
            "executor": self.executor.value,
            "executor_reason": self.executor_reason,
            "priority": self.priority,
            "estimated_effort": self.estimated_effort,
        }


@dataclass
class ActionPlan:
    """行動計画."""

    topic: str
    read_items: list[ActionItem] = field(default_factory=list)
    build_items: list[ActionItem] = field(default_factory=list)
    ignore_items: list[ActionItem] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Markdown形式で出力."""
        lines = [f"# Action Plan: {self.topic}\n"]

        if self.read_items:
            lines.append("## READ (読む)\n")
            for item in self.read_items:
                lines.append(f"- **{item.target}**")
                lines.append(f"  - 理由: {item.reason}")
                lines.append(f"  - 担当: {item.executor.value} ({item.executor_reason})")
                lines.append("")

        if self.build_items:
            lines.append("## BUILD (作る)\n")
            for item in self.build_items:
                lines.append(f"- **{item.target}**")
                lines.append(f"  - 理由: {item.reason}")
                lines.append(f"  - 担当: {item.executor.value} ({item.executor_reason})")
                if item.estimated_effort:
                    lines.append(f"  - 見積もり: {item.estimated_effort}")
                lines.append("")

        if self.ignore_items:
            lines.append("## IGNORE (捨てる)\n")
            for item in self.ignore_items:
                lines.append(f"- **{item.target}**")
                lines.append(f"  - 理由: {item.reason}")
                lines.append("")

        return "\n".join(lines)


class ActionPlanner:
    """行動計画器.

    新テーマに対して：
    - 何を読むべきか
    - 何を作るべきか
    - 何を捨ててよいか
    を理由付きで提示。
    """

    def plan(
        self, topic: str, candidates: list[dict[str, Any]], context: str | None = None
    ) -> ActionPlan:
        """
        行動計画を作成.

        Args:
            topic: トピック
            candidates: 候補リスト（各候補はtitle, type, relevance等を持つ）
            context: コンテキスト

        Returns:
            ActionPlan
        """
        plan = ActionPlan(topic=topic)

        for c in candidates:
            action, item = self._classify_candidate(c)

            if action == ActionType.READ:
                plan.read_items.append(item)
            elif action == ActionType.BUILD:
                plan.build_items.append(item)
            else:
                plan.ignore_items.append(item)

        # 優先度でソート
        plan.read_items.sort(key=lambda x: x.priority, reverse=True)
        plan.build_items.sort(key=lambda x: x.priority, reverse=True)

        logger.info(
            f"Created action plan for {topic}: "
            f"READ={len(plan.read_items)}, "
            f"BUILD={len(plan.build_items)}, "
            f"IGNORE={len(plan.ignore_items)}"
        )

        return plan

    def _classify_candidate(self, candidate: dict[str, Any]) -> tuple[ActionType, ActionItem]:
        """候補を分類."""
        title = candidate.get("title", "Unknown")
        c_type = candidate.get("type", "paper")
        relevance = candidate.get("relevance", 3)
        evidence = candidate.get("evidence", 3)

        # 分類ルール
        if relevance < 2:
            action = ActionType.IGNORE
            reason = "関連度が低い"
            executor = Executor.AI
            executor_reason = "自動判定で十分"
        elif c_type == "paper" and evidence >= 3:
            action = ActionType.READ
            reason = "根拠が強く、読む価値あり"
            executor = Executor.HUMAN
            executor_reason = "理解と判断は人間が行う"
        elif c_type == "code" or c_type == "implementation":
            action = ActionType.BUILD
            reason = "実装候補"
            executor = Executor.AI
            executor_reason = "コード生成はAIが効率的"
        else:
            action = ActionType.READ
            reason = "情報収集のため"
            executor = Executor.BOTH
            executor_reason = "AIが要約、人間が判断"

        item = ActionItem(
            action_type=action,
            target=title,
            reason=reason,
            executor=executor,
            executor_reason=executor_reason,
            priority=relevance,
        )

        return action, item

    def quick_plan(
        self,
        topic: str,
        top_papers: list[str],
        implementation_ideas: list[str],
        low_priority: list[str],
    ) -> ActionPlan:
        """
        簡易行動計画を作成.

        Args:
            topic: トピック
            top_papers: 読むべき論文リスト
            implementation_ideas: 作るべきアイデアリスト
            low_priority: 捨ててよいリスト

        Returns:
            ActionPlan
        """
        plan = ActionPlan(topic=topic)

        for paper in top_papers:
            plan.read_items.append(
                ActionItem(
                    action_type=ActionType.READ,
                    target=paper,
                    reason="Top priority paper",
                    executor=Executor.HUMAN,
                    executor_reason="理解は人間が行う",
                    priority=5,
                )
            )

        for idea in implementation_ideas:
            plan.build_items.append(
                ActionItem(
                    action_type=ActionType.BUILD,
                    target=idea,
                    reason="Implementation candidate",
                    executor=Executor.AI,
                    executor_reason="コード生成はAI",
                    priority=4,
                )
            )

        for item in low_priority:
            plan.ignore_items.append(
                ActionItem(
                    action_type=ActionType.IGNORE,
                    target=item,
                    reason="Low relevance or outdated",
                    executor=Executor.AI,
                    executor_reason="自動除外",
                    priority=1,
                )
            )

        return plan