"""
JARVIS Multi-Judge Evaluator

複数Judge + 反証役（Counterfactual）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class JudgeRole(Enum):
    """Judge役割."""
    STRICT_REVIEWER = "strict_reviewer"  # 厳格査読者
    PRACTICAL_PM = "practical_pm"         # 実務PM
    COUNTERFACTUAL = "counterfactual"     # 反証役


class DisqualificationReason(Enum):
    """失格理由."""
    NO_EVIDENCE = "no_evidence"           # 根拠なき断言
    UNKNOWN_SOURCE = "unknown_source"     # 出典不明
    NOT_REPRODUCIBLE = "not_reproducible" # 再現性なし
    BIAS_DETECTED = "bias_detected"       # バイアス検出
    CLAIM_MISMATCH = "claim_mismatch"     # 主張と根拠の不一致


@dataclass
class JudgeVerdict:
    """Judge判定."""
    judge_role: JudgeRole
    approved: bool
    score: float  # 0.0 - 1.0
    reasoning: str
    disqualifications: list[DisqualificationReason] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """評価結果."""
    item_id: str
    verdicts: list[JudgeVerdict]
    final_approved: bool
    final_score: float
    disqualified: bool
    disqualification_reasons: list[DisqualificationReason] = field(default_factory=list)

    @property
    def consensus_score(self) -> float:
        """合意スコア（全Judgeの平均）."""
        if not self.verdicts:
            return 0.0
        return sum(v.score for v in self.verdicts) / len(self.verdicts)


class MultiJudgeEvaluator:
    """Multi-Judge評価器.
    
    Judge種別:
    - 厳格査読者: 学術的正確性を重視
    - 実務PM: 実用性・コストを重視
    - 反証役: 反例・弱点を探す
    
    失格条件:
    - 根拠なき断言
    - 出典不明
    - 再現性なし
    """

    def __init__(self):
        """初期化."""
        self._judges = [
            JudgeRole.STRICT_REVIEWER,
            JudgeRole.PRACTICAL_PM,
            JudgeRole.COUNTERFACTUAL,
        ]

    def evaluate(
        self,
        item_id: str,
        content: str,
        evidence: list[str],
        metadata: dict[str, Any] | None = None
    ) -> EvaluationResult:
        """
        アイテムを評価.
        
        Args:
            item_id: アイテムID
            content: 評価対象の内容
            evidence: 根拠リスト
            metadata: メタデータ
        
        Returns:
            EvaluationResult
        """
        verdicts = []

        for judge_role in self._judges:
            verdict = self._judge(judge_role, content, evidence, metadata)
            verdicts.append(verdict)

        # 最終判定
        all_approved = all(v.approved for v in verdicts)
        all_disqualifications = []
        for v in verdicts:
            all_disqualifications.extend(v.disqualifications)

        # 失格チェック
        disqualified = len(all_disqualifications) > 0

        # 最終スコア（失格なら0）
        final_score = 0.0 if disqualified else sum(v.score for v in verdicts) / len(verdicts)

        return EvaluationResult(
            item_id=item_id,
            verdicts=verdicts,
            final_approved=all_approved and not disqualified,
            final_score=final_score,
            disqualified=disqualified,
            disqualification_reasons=list(set(all_disqualifications)),
        )

    def _judge(
        self,
        role: JudgeRole,
        content: str,
        evidence: list[str],
        metadata: dict[str, Any] | None
    ) -> JudgeVerdict:
        """単一Judgeの判定."""

        disqualifications = []
        suggestions = []

        # 失格条件チェック
        if not evidence:
            disqualifications.append(DisqualificationReason.NO_EVIDENCE)

        if role == JudgeRole.STRICT_REVIEWER:
            verdict = self._strict_review(content, evidence, disqualifications, suggestions)
        elif role == JudgeRole.PRACTICAL_PM:
            verdict = self._practical_review(content, evidence, disqualifications, suggestions)
        else:  # COUNTERFACTUAL
            verdict = self._counterfactual_review(content, evidence, disqualifications, suggestions)

        verdict.disqualifications = disqualifications
        verdict.suggestions = suggestions

        return verdict

    def _strict_review(
        self,
        content: str,
        evidence: list[str],
        disqualifications: list[DisqualificationReason],
        suggestions: list[str]
    ) -> JudgeVerdict:
        """厳格査読者の判定."""

        # 根拠の質をチェック
        score = 0.0
        if evidence:
            score = min(1.0, len(evidence) * 0.3)

        # 断言チェック（簡易）
        assertive_words = ["確実に", "絶対に", "必ず", "certainly", "definitely"]
        for word in assertive_words:
            if word in content.lower():
                if not evidence:
                    disqualifications.append(DisqualificationReason.NO_EVIDENCE)
                suggestions.append(f"Avoid assertive language: {word}")

        approved = len(disqualifications) == 0 and score >= 0.6

        return JudgeVerdict(
            judge_role=JudgeRole.STRICT_REVIEWER,
            approved=approved,
            score=score,
            reasoning="Strict academic review",
        )

    def _practical_review(
        self,
        content: str,
        evidence: list[str],
        disqualifications: list[DisqualificationReason],
        suggestions: list[str]
    ) -> JudgeVerdict:
        """実務PMの判定."""

        # 実用性をチェック（プレースホルダー）
        score = 0.7 if evidence else 0.3

        approved = score >= 0.5

        return JudgeVerdict(
            judge_role=JudgeRole.PRACTICAL_PM,
            approved=approved,
            score=score,
            reasoning="Practical implementation review",
        )

    def _counterfactual_review(
        self,
        content: str,
        evidence: list[str],
        disqualifications: list[DisqualificationReason],
        suggestions: list[str]
    ) -> JudgeVerdict:
        """反証役の判定."""

        # 反例を探す（プレースホルダー）
        score = 0.6

        suggestions.append("Consider alternative interpretations")

        if not evidence:
            suggestions.append("No evidence provided - claims cannot be verified")

        approved = True  # 反証役は常に提案を出すが、自体は承認する

        return JudgeVerdict(
            judge_role=JudgeRole.COUNTERFACTUAL,
            approved=approved,
            score=score,
            reasoning="Counterfactual analysis",
        )
