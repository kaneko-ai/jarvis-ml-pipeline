"""
JARVIS Pattern Extractor

Phase 2: 判断パターン抽出
- Decisionをクラスタリングし「型」を抽出
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .decision_item import DecisionItem, DecisionPattern, DecisionStore

logger = logging.getLogger(__name__)


@dataclass
class PatternSummary:
    """パターンサマリー."""
    pattern: DecisionPattern
    count: int
    success_rate: float
    description: str
    example_contexts: list[str]


class PatternExtractor:
    """判断パターン抽出器.
    
    Decisionをクラスタリングし、判断の「型」を抽出。
    """

    # パターン説明
    PATTERN_DESCRIPTIONS = {
        DecisionPattern.EARLY_STAGE_REJECT: "流行初期・根拠不足のため保留",
        DecisionPattern.HIGH_EFFORT_DELAY: "導入コストが高いため後回し",
        DecisionPattern.EVALUATOR_FIRST: "評価系を先に強化",
        DecisionPattern.CORE_PRIORITY: "中核機能を優先採用",
        DecisionPattern.EVIDENCE_REQUIRED: "根拠を揃えてから再検討",
        DecisionPattern.UNCLASSIFIED: "未分類",
    }

    def __init__(self, store: Optional[DecisionStore] = None):
        """
        初期化.
        
        Args:
            store: DecisionStore
        """
        self.store = store or DecisionStore()

    def classify(self, decision: DecisionItem) -> DecisionPattern:
        """
        Decisionをパターン分類.
        
        Args:
            decision: 判断
        
        Returns:
            DecisionPattern
        """
        reason_lower = decision.reason.lower()
        context_lower = decision.context.lower()

        # ルールベース分類
        if "evidence" in reason_lower or "根拠" in reason_lower:
            if decision.decision == "reject":
                return DecisionPattern.EVIDENCE_REQUIRED
            return DecisionPattern.UNCLASSIFIED

        if "effort" in reason_lower or "コスト" in reason_lower:
            return DecisionPattern.HIGH_EFFORT_DELAY

        if "evaluator" in context_lower or "評価" in context_lower:
            if decision.decision == "accept":
                return DecisionPattern.EVALUATOR_FIRST

        if "core" in context_lower or "中核" in context_lower:
            if decision.decision == "accept":
                return DecisionPattern.CORE_PRIORITY

        if "early" in reason_lower or "初期" in reason_lower:
            return DecisionPattern.EARLY_STAGE_REJECT

        return DecisionPattern.UNCLASSIFIED

    def extract_summaries(self) -> list[PatternSummary]:
        """
        全パターンのサマリーを抽出.
        
        Returns:
            PatternSummary リスト
        """
        decisions = self.store.list_all()

        # パターンごとに集計
        pattern_decisions: dict[DecisionPattern, list[DecisionItem]] = {}
        for d in decisions:
            if d.pattern not in pattern_decisions:
                pattern_decisions[d.pattern] = []
            pattern_decisions[d.pattern].append(d)

        summaries = []
        for pattern, items in pattern_decisions.items():
            # 成功率計算
            outcomes = [d.outcome_status for d in items if d.outcome_status]
            success_count = sum(1 for o in outcomes if o == "success")
            success_rate = success_count / len(outcomes) if outcomes else 0.0

            # 例のコンテキスト
            examples = [d.context[:50] for d in items[:3]]

            summaries.append(PatternSummary(
                pattern=pattern,
                count=len(items),
                success_rate=success_rate,
                description=self.PATTERN_DESCRIPTIONS.get(pattern, ""),
                example_contexts=examples,
            ))

        # カウント降順でソート
        summaries.sort(key=lambda x: x.count, reverse=True)

        return summaries

    def get_pattern_advice(self, pattern: DecisionPattern) -> str:
        """
        パターンに基づくアドバイスを取得.
        
        Args:
            pattern: パターン
        
        Returns:
            アドバイス文字列
        """
        advice_map = {
            DecisionPattern.EARLY_STAGE_REJECT:
                "このパターンは根拠が揃うまで保留がベスト。急いで採用すると後悔する傾向。",
            DecisionPattern.HIGH_EFFORT_DELAY:
                "コストが高い場合は後回しが正解。他の改善を先にやると効率的。",
            DecisionPattern.EVALUATOR_FIRST:
                "評価系の改善は優先度高。判断精度が上がると全体が良くなる。",
            DecisionPattern.CORE_PRIORITY:
                "中核機能の改善は積極採用。Javisの本質的強化につながる。",
            DecisionPattern.EVIDENCE_REQUIRED:
                "根拠が不足。追加調査をしてから再検討。",
            DecisionPattern.UNCLASSIFIED:
                "パターン未確定。慎重に判断。",
        }
        return advice_map.get(pattern, "")
