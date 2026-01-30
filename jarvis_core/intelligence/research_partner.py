"""
JARVIS Research Partner Mode

Phase4-7 統合版: 研究パートナーAI
- Phase4: 問い生成 + 行動計画
- Phase5: Long-term Memory参照
- Phase6: 戦略的示唆
- Phase7: 自己改善提案

役割: 「答えること」ではなく、人間が最短で判断できる状態を作る
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .action_planner import ActionItem, ActionPlan, ActionPlanner, ActionType, Executor
from .decision_item import DecisionStore
from .goldset_index import GoldsetEntry, GoldsetIndex
from .outcome_tracker import OutcomeTracker
from .question_generator import QuestionGenerator

logger = logging.getLogger(__name__)


class StrategicAssessment(Enum):
    """戦略評価."""

    GO = "go"  # 攻めるべき
    HOLD = "hold"  # 様子見
    NO_GO = "no_go"  # 捨てるべき


@dataclass
class KeyQuestions:
    """Phase4: 問い生成."""

    unverified: str  # 未検証の問い
    implicit_assumption: str  # 暗黙の前提
    decision_point: str  # 分岐点


@dataclass
class PastDecisionReference:
    """Phase5: 過去判断参照."""

    decision_id: str
    original_decision: str
    outcome: str
    implication_for_now: str  # 今回への示唆


@dataclass
class StrategicSuggestion:
    """Phase6: 戦略的示唆."""

    assessment: StrategicAssessment
    reasoning: str
    roi_evaluation: str  # 時間×学習価値×将来性


@dataclass
class ImprovementSuggestion:
    """Phase7: 自己改善提案."""

    suggestion: str
    category: str  # evaluation_axis, speed, feature


@dataclass
class ResearchPartnerOutput:
    """Research Partner 出力."""

    # 入力
    theme: str
    constraints: str | None = None

    # Phase4
    key_questions: KeyQuestions | None = None
    action_plan: ActionPlan | None = None

    # Phase5
    past_decisions: list[PastDecisionReference] = field(default_factory=list)

    # Phase6
    strategic: StrategicSuggestion | None = None

    # Phase7
    improvements: list[ImprovementSuggestion] = field(default_factory=list)

    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        """固定フォーマットで出力."""
        lines = [
            "# Research Partner Report",
            f"**Theme**: {self.theme}",
        ]
        if self.constraints:
            lines.append(f"**Constraints**: {self.constraints}")
        lines.append("")

        # Phase4: Key Questions
        if self.key_questions:
            lines.extend(
                [
                    "## 【Key Questions】",
                    f"**Q1 (未検証)**: {self.key_questions.unverified}",
                    f"**Q2 (暗黙の前提)**: {self.key_questions.implicit_assumption}",
                    f"**Q3 (分岐点)**: {self.key_questions.decision_point}",
                    "",
                ]
            )

        # Phase4: Action Plan
        if self.action_plan:
            lines.append("## 【READ】")
            for item in self.action_plan.read_items[:5]:
                lines.append(f"- **{item.target}**: {item.reason}")
            lines.append("")

            lines.append("## 【BUILD】")
            for item in self.action_plan.build_items[:3]:
                lines.append(f"- **{item.target}**: {item.reason}")
            lines.append("")

            lines.append("## 【IGNORE】")
            for item in self.action_plan.ignore_items[:3]:
                lines.append(f"- **{item.target}**: {item.reason}")
            lines.append("")

        # Phase5: Past Decisions
        if self.past_decisions:
            lines.append("## 【Past Decisions Referenced】")
            for pd in self.past_decisions[:3]:
                lines.extend(
                    [
                        f"- **{pd.decision_id}**",
                        f"  - 当時の判断: {pd.original_decision}",
                        f"  - Outcome: {pd.outcome}",
                        f"  - 今回への示唆: {pd.implication_for_now}",
                    ]
                )
            lines.append("")

        # Phase6: Strategic Assessment
        if self.strategic:
            lines.extend(
                [
                    "## 【Strategic Assessment】",
                    f"- **{self.strategic.assessment.value.upper()}**",
                    f"- 理由: {self.strategic.reasoning}",
                    f"- ROI評価: {self.strategic.roi_evaluation}",
                    "",
                ]
            )

        # Phase7: Self-Improvement
        if self.improvements:
            lines.append("## 【System Improvement Suggestions】")
            for i, imp in enumerate(self.improvements[:2], 1):
                lines.append(f"- Suggestion {i}: {imp.suggestion}")
            lines.append("")

        return "\n".join(lines)


class ResearchPartner:
    """Research Partner AI.

    役割（重要）:
    - 「答えること」ではない
    - 人間が何を読む/作る/捨てるかを最短で判断できる状態を作る

    厳守事項:
    - 流行・網羅性・包括的説明を優先しない
    - 「やらない判断」を積極的に提示
    - 不確実性を隠さず、前提と限界を明示
    - Phase1-3の Decision/Goldset/Outcome を必ず参照
    """

    def __init__(
        self,
        goldset_index: GoldsetIndex | None = None,
        decision_store: DecisionStore | None = None,
        outcome_tracker: OutcomeTracker | None = None,
    ):
        """初期化."""
        self.goldset_index = goldset_index or GoldsetIndex()
        self.decision_store = decision_store or DecisionStore()
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.question_generator = QuestionGenerator()
        self.action_planner = ActionPlanner()

    def consult(
        self,
        theme: str,
        constraints: str | None = None,
        current_situation: str | None = None,
    ) -> ResearchPartnerOutput:
        """
        研究相談を実行.

        Args:
            theme: 研究テーマ（1行）
            constraints: 制約条件
            current_situation: 現在の状況

        Returns:
            ResearchPartnerOutput
        """
        logger.info(f"Research Partner consultation: {theme}")

        # Phase5: 過去判断を先に参照（判断の前に必ず実行）
        past_decisions = self._reference_past_decisions(theme)

        # Phase4: 問い生成
        key_questions = self._generate_key_questions(theme, current_situation)

        # Phase4: 行動計画
        action_plan = self._create_action_plan(theme, constraints, past_decisions)

        # Phase6: 戦略的示唆
        strategic = self._assess_strategy(theme, past_decisions)

        # Phase7: 自己改善提案
        improvements = self._suggest_improvements(theme, past_decisions)

        return ResearchPartnerOutput(
            theme=theme,
            constraints=constraints,
            key_questions=key_questions,
            action_plan=action_plan,
            past_decisions=past_decisions,
            strategic=strategic,
            improvements=improvements,
        )

    def _reference_past_decisions(self, theme: str) -> list[PastDecisionReference]:
        """Phase5: 過去判断を参照（最低2件）."""
        references = []

        # Goldsetから類似判断を検索
        goldset_results = self.goldset_index.search(theme, top_k=2)
        for entry, similarity in goldset_results:
            references.append(
                PastDecisionReference(
                    decision_id=f"goldset_{hash(entry.context) % 10000}",
                    original_decision=f"{entry.decision}: {entry.reason}",
                    outcome=entry.outcome,
                    implication_for_now=self._derive_implication(entry, theme),
                )
            )

        # DecisionStoreからも追加
        decisions = self.decision_store.list_all()[-5:]
        for d in decisions[:2]:
            if d.outcome:
                references.append(
                    PastDecisionReference(
                        decision_id=d.decision_id,
                        original_decision=f"{d.decision}: {d.reason}",
                        outcome=d.outcome or "未評価",
                        implication_for_now="過去の判断パターンとして参照",
                    )
                )

        return references[:3]  # 最大3件

    def _derive_implication(self, entry: GoldsetEntry, theme: str) -> str:
        """今回への示唆を導出."""
        if entry.decision == "reject":
            return "類似ケースでは見送りが正解だった。今回も慎重に。"
        else:
            return "類似ケースでは採用が成功した。条件が合えば検討価値あり。"

    def _generate_key_questions(self, theme: str, current_situation: str | None) -> KeyQuestions:
        """Phase4: 問い生成."""

        return KeyQuestions(
            unverified=f"「{theme}」で未検証だが価値がありそうな仮説は何か？",
            implicit_assumption="この分野で「当たり前」とされている前提は妥当か？",
            decision_point="今ここで判断を誤ると後戻りが難しい選択は何か？",
        )

    def _create_action_plan(
        self, theme: str, constraints: str | None, past_decisions: list[PastDecisionReference]
    ) -> ActionPlan:
        """Phase4: 行動計画."""
        plan = ActionPlan(topic=theme)

        # READ: 今読むべきもの
        plan.read_items = [
            ActionItem(
                action_type=ActionType.READ,
                target=f"{theme}の基礎論文（代表的なreview）",
                reason="まず全体像を把握する必要がある",
                executor=Executor.HUMAN,
                executor_reason="理解と判断は人間が行う",
                priority=5,
            ),
            ActionItem(
                action_type=ActionType.READ,
                target="最新のbenchmark/evaluation論文",
                reason="現在の評価基準を知る必要がある",
                executor=Executor.HUMAN,
                executor_reason="評価軸の理解は人間",
                priority=4,
            ),
        ]

        # BUILD: 作る/試す
        plan.build_items = [
            ActionItem(
                action_type=ActionType.BUILD,
                target=f"最小限の検証コード（{theme}関連）",
                reason="論文を読むより手を動かす方が早い場合がある",
                executor=Executor.AI,
                executor_reason="コード生成はAI",
                priority=4,
            ),
        ]

        # IGNORE: 捨てる
        # 過去判断を参照して捨てるべきものを特定
        ignore_reasons = []
        for pd in past_decisions:
            if "reject" in pd.original_decision.lower():
                ignore_reasons.append(pd.implication_for_now)

        plan.ignore_items = [
            ActionItem(
                action_type=ActionType.IGNORE,
                target="再現性のないプレプリント",
                reason="根拠不足。過去の判断でも見送りが正解だった。",
                executor=Executor.AI,
                executor_reason="自動除外",
                priority=1,
            ),
            ActionItem(
                action_type=ActionType.IGNORE,
                target="関連度の低い周辺トピック",
                reason="時間対効果が低い。中核テーマに集中。",
                executor=Executor.AI,
                executor_reason="自動除外",
                priority=1,
            ),
        ]

        return plan

    def _assess_strategy(
        self, theme: str, past_decisions: list[PastDecisionReference]
    ) -> StrategicSuggestion:
        """Phase6: 戦略的示唆."""
        # 過去判断から傾向を分析
        reject_count = sum(1 for pd in past_decisions if "reject" in pd.original_decision.lower())

        if reject_count >= 2:
            assessment = StrategicAssessment.HOLD
            reasoning = "類似ケースで見送りが多い。慎重に条件を確認すべき。"
        elif reject_count == 1:
            assessment = StrategicAssessment.HOLD
            reasoning = "一部に懸念あり。限定的に試すのが妥当。"
        else:
            assessment = StrategicAssessment.GO
            reasoning = "過去の成功パターンと合致。積極的に取り組む価値あり。"

        roi_evaluation = "時間投資に対する学習価値は中〜高。将来性は要確認。"

        return StrategicSuggestion(
            assessment=assessment,
            reasoning=reasoning,
            roi_evaluation=roi_evaluation,
        )

    def _suggest_improvements(
        self, theme: str, past_decisions: list[PastDecisionReference]
    ) -> list[ImprovementSuggestion]:
        """Phase7: 自己改善提案."""
        suggestions = []

        # 過去判断が少ない場合
        if len(past_decisions) < 2:
            suggestions.append(
                ImprovementSuggestion(
                    suggestion="Goldset/DecisionItemの蓄積が不足。判断を積み重ねることで精度向上。",
                    category="data",
                )
            )

        # 評価軸の改善
        suggestions.append(
            ImprovementSuggestion(
                suggestion=f"「{theme}」に特化した評価軸を追加すると判断が鋭くなる可能性。",
                category="evaluation_axis",
            )
        )

        return suggestions[:2]
