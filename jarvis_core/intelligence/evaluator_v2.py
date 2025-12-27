"""
JARVIS Intelligent Evaluator V2

Phase 1: 5軸評価（Relevance/Novelty/Evidence/Effort/Risk）
- すべてのIssue/提案に必須
- 0-5点 + 理由1文
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EvaluationAxis(Enum):
    """評価軸（5軸固定）."""
    RELEVANCE = "relevance"      # Javisとの関連度
    NOVELTY = "novelty"          # 新規性
    EVIDENCE = "evidence"        # 根拠の強さ
    EFFORT = "effort"            # 導入コスト
    RISK = "risk"                # リスク


@dataclass
class AxisScore:
    """軸ごとのスコア."""
    axis: EvaluationAxis
    score: int  # 0-5
    reason: str  # 理由1文
    
    def __post_init__(self):
        if not 0 <= self.score <= 5:
            raise ValueError(f"Score must be 0-5, got {self.score}")


@dataclass
class ScoreBreakdown:
    """5軸評価の内訳.
    
    すべてのIssue/提案に必須出力。
    """
    relevance: AxisScore
    novelty: AxisScore
    evidence: AxisScore
    effort: AxisScore
    risk: AxisScore
    
    @property
    def total(self) -> int:
        """合計スコア."""
        return (
            self.relevance.score +
            self.novelty.score +
            self.evidence.score +
            self.effort.score +
            self.risk.score
        )
    
    @property
    def average(self) -> float:
        """平均スコア."""
        return self.total / 5.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換."""
        return {
            "relevance": {"score": self.relevance.score, "reason": self.relevance.reason},
            "novelty": {"score": self.novelty.score, "reason": self.novelty.reason},
            "evidence": {"score": self.evidence.score, "reason": self.evidence.reason},
            "effort": {"score": self.effort.score, "reason": self.effort.reason},
            "risk": {"score": self.risk.score, "reason": self.risk.reason},
            "total": self.total,
            "average": self.average,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoreBreakdown":
        """辞書から生成."""
        return cls(
            relevance=AxisScore(EvaluationAxis.RELEVANCE, data["relevance"]["score"], data["relevance"]["reason"]),
            novelty=AxisScore(EvaluationAxis.NOVELTY, data["novelty"]["score"], data["novelty"]["reason"]),
            evidence=AxisScore(EvaluationAxis.EVIDENCE, data["evidence"]["score"], data["evidence"]["reason"]),
            effort=AxisScore(EvaluationAxis.EFFORT, data["effort"]["score"], data["effort"]["reason"]),
            risk=AxisScore(EvaluationAxis.RISK, data["risk"]["score"], data["risk"]["reason"]),
        )


class IntelligentEvaluator:
    """知能評価器.
    
    5軸評価を必須出力。
    """
    
    # 評価基準ガイド
    AXIS_GUIDE = {
        EvaluationAxis.RELEVANCE: {
            5: "中核機能（評価・記憶・探索）を直接強化",
            4: "中核機能を間接的に強化",
            3: "補助的（DX・速度改善など）",
            2: "周辺機能の改善",
            1: "本質からズレる",
        },
        EvaluationAxis.NOVELTY: {
            5: "概念レベルで新しい（未導入）",
            4: "新しいアプローチ",
            3: "既存の改善・拡張",
            2: "マイナー改善",
            1: "すでに実装済み/陳腐",
        },
        EvaluationAxis.EVIDENCE: {
            5: "査読論文＋再現コード",
            4: "査読論文のみ",
            3: "実装報告・事例",
            2: "技術ブログ",
            1: "SNS・主観",
        },
        EvaluationAxis.EFFORT: {
            5: "1日以内・小改修",
            4: "2-3日・局所変更",
            3: "数日・複数ファイル",
            2: "1週間以上",
            1: "大規模改修・破壊的",
        },
        EvaluationAxis.RISK: {
            5: "影響なし/ロールバック容易",
            4: "軽微な影響",
            3: "一部機能劣化の可能性",
            2: "複数機能に影響",
            1: "OS構造・データ破壊",
        },
    }
    
    def evaluate(
        self,
        title: str,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ScoreBreakdown:
        """
        5軸評価を実行.
        
        Args:
            title: 提案タイトル
            description: 詳細説明
            context: 追加コンテキスト
        
        Returns:
            ScoreBreakdown
        """
        # ルールベース評価（プレースホルダー）
        # 本番はLLMで評価
        
        relevance = self._evaluate_axis(
            EvaluationAxis.RELEVANCE,
            title, description, context
        )
        novelty = self._evaluate_axis(
            EvaluationAxis.NOVELTY,
            title, description, context
        )
        evidence = self._evaluate_axis(
            EvaluationAxis.EVIDENCE,
            title, description, context
        )
        effort = self._evaluate_axis(
            EvaluationAxis.EFFORT,
            title, description, context
        )
        risk = self._evaluate_axis(
            EvaluationAxis.RISK,
            title, description, context
        )
        
        breakdown = ScoreBreakdown(
            relevance=relevance,
            novelty=novelty,
            evidence=evidence,
            effort=effort,
            risk=risk,
        )
        
        logger.info(f"Evaluated '{title}': total={breakdown.total}, avg={breakdown.average:.1f}")
        return breakdown
    
    def _evaluate_axis(
        self,
        axis: EvaluationAxis,
        title: str,
        description: str,
        context: Optional[Dict[str, Any]]
    ) -> AxisScore:
        """単一軸を評価."""
        text = f"{title} {description}".lower()
        
        # ルールベース（プレースホルダー）
        if axis == EvaluationAxis.RELEVANCE:
            score = self._score_relevance(text)
        elif axis == EvaluationAxis.NOVELTY:
            score = self._score_novelty(text)
        elif axis == EvaluationAxis.EVIDENCE:
            score = self._score_evidence(text, context)
        elif axis == EvaluationAxis.EFFORT:
            score = self._score_effort(text)
        else:  # RISK
            score = self._score_risk(text)
        
        reason = self.AXIS_GUIDE[axis].get(score, "評価中")
        
        return AxisScore(axis=axis, score=score, reason=reason)
    
    def _score_relevance(self, text: str) -> int:
        """関連度をスコアリング."""
        core_keywords = ["evaluator", "memory", "decision", "judge", "ranking"]
        matches = sum(1 for kw in core_keywords if kw in text)
        return min(5, 2 + matches)
    
    def _score_novelty(self, text: str) -> int:
        """新規性をスコアリング."""
        new_keywords = ["new", "novel", "first", "初", "新規"]
        matches = sum(1 for kw in new_keywords if kw in text)
        return min(5, 3 + matches)
    
    def _score_evidence(self, text: str, context: Optional[Dict]) -> int:
        """根拠をスコアリング."""
        if context and context.get("has_paper"):
            return 4
        if "doi:" in text or "arxiv" in text or "pubmed" in text:
            return 4
        if "github" in text:
            return 3
        return 2
    
    def _score_effort(self, text: str) -> int:
        """導入コストをスコアリング."""
        if "minor" in text or "小" in text:
            return 5
        if "破壊" in text or "breaking" in text:
            return 1
        return 3
    
    def _score_risk(self, text: str) -> int:
        """リスクをスコアリング."""
        if "破壊" in text or "danger" in text:
            return 1
        if "safe" in text or "安全" in text:
            return 5
        return 4
