"""
JARVIS Question Generator

Phase 4: 問い生成
- 未検証点は何か
- 既存手法の前提は何か
- 次に検証すべき仮説は何か
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """問いのタイプ."""
    UNVERIFIED = "unverified"        # 未検証点
    ASSUMPTION = "assumption"         # 既存の前提
    HYPOTHESIS = "hypothesis"         # 検証すべき仮説
    GAP = "gap"                       # 知識のギャップ
    NEXT_STEP = "next_step"           # 次のステップ


@dataclass
class ResearchQuestion:
    """研究上の問い."""
    question_type: QuestionType
    question: str
    context: str
    priority: int  # 1-5 (5が最高)
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "type": self.question_type.value,
            "question": self.question,
            "context": self.context,
            "priority": self.priority,
            "reasoning": self.reasoning,
        }


class QuestionGenerator:
    """問い生成器.
    
    新テーマに対して：
    - 未検証点を特定
    - 前提を洗い出し
    - 次の仮説を提示
    """

    # 問い生成テンプレート
    QUESTION_TEMPLATES = {
        QuestionType.UNVERIFIED: [
            "この分野で未検証なのは何か？",
            "実験的に確認されていない主張は？",
            "他の条件で成り立つか確認されているか？",
        ],
        QuestionType.ASSUMPTION: [
            "既存手法の前提は何か？",
            "暗黙の仮定は何か？",
            "この結論が依存している条件は？",
        ],
        QuestionType.HYPOTHESIS: [
            "次に検証すべき仮説は何か？",
            "反証可能な形で仮説を立てるとどうなるか？",
            "この仮説が正しければ何が予測されるか？",
        ],
        QuestionType.GAP: [
            "現在の知識で説明できないことは？",
            "データが不足している領域は？",
            "矛盾する報告はあるか？",
        ],
        QuestionType.NEXT_STEP: [
            "次に調べるべきことは？",
            "優先的に取り組むべき問題は？",
            "短期的に解決可能な課題は？",
        ],
    }

    def generate(
        self,
        topic: str,
        context: str | None = None,
        existing_knowledge: list[str] | None = None
    ) -> list[ResearchQuestion]:
        """
        問いを生成.
        
        Args:
            topic: トピック
            context: コンテキスト
            existing_knowledge: 既存知識リスト
        
        Returns:
            ResearchQuestion リスト
        """
        questions = []

        # 各タイプの問いを生成
        for q_type in QuestionType:
            q = self._generate_for_type(q_type, topic, context, existing_knowledge)
            if q:
                questions.append(q)

        # 優先度でソート
        questions.sort(key=lambda x: x.priority, reverse=True)

        logger.info(f"Generated {len(questions)} questions for topic: {topic}")
        return questions

    def _generate_for_type(
        self,
        q_type: QuestionType,
        topic: str,
        context: str | None,
        existing_knowledge: list[str] | None
    ) -> ResearchQuestion | None:
        """タイプ別に問いを生成."""
        templates = self.QUESTION_TEMPLATES.get(q_type, [])
        if not templates:
            return None

        # トピックに応じて問いを選択（プレースホルダー）
        # 本番ではLLMで生成
        template = templates[0]
        question = f"【{topic}】{template}"

        # 優先度決定（簡易）
        priority = self._calc_priority(q_type, topic, existing_knowledge)

        return ResearchQuestion(
            question_type=q_type,
            question=question,
            context=context or topic,
            priority=priority,
            reasoning=f"Generated from {q_type.value} template",
        )

    def _calc_priority(
        self,
        q_type: QuestionType,
        topic: str,
        existing_knowledge: list[str] | None
    ) -> int:
        """優先度を計算."""
        # 基本優先度
        base_priority = {
            QuestionType.HYPOTHESIS: 5,
            QuestionType.NEXT_STEP: 4,
            QuestionType.GAP: 4,
            QuestionType.UNVERIFIED: 3,
            QuestionType.ASSUMPTION: 2,
        }

        priority = base_priority.get(q_type, 3)

        # 既存知識が少ないほど優先度上げる
        if not existing_knowledge or len(existing_knowledge) < 3:
            priority = min(5, priority + 1)

        return priority

    def format_for_output(self, questions: list[ResearchQuestion]) -> str:
        """出力用にフォーマット."""
        if not questions:
            return "No questions generated."

        lines = ["# Research Questions\n"]

        for i, q in enumerate(questions, 1):
            lines.append(f"## {i}. [{q.question_type.value.upper()}] (Priority: {q.priority})")
            lines.append(f"**{q.question}**")
            lines.append("")
            lines.append(f"*Reasoning*: {q.reasoning}")
            lines.append("")

        return "\n".join(lines)
