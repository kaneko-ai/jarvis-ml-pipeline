"""
JARVIS Decision Module

Phase 1: 判断ルールと Reject Reason
- accept/reject を必ず決定
- reject には理由分類必須
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .evaluator_v2 import ScoreBreakdown

logger = logging.getLogger(__name__)


class DecisionStatus(Enum):
    """判断ステータス."""

    ACCEPT = "accept"
    REJECT = "reject"
    PENDING = "pending"  # 保留（最終的には使わない）


class RejectReason(Enum):
    """Reject理由分類（6種固定）.

    曖昧な reject を禁止。
    """

    EVIDENCE_INSUFFICIENT = "evidence_insufficient"  # 根拠不足
    RELEVANCE_LOW = "relevance_low"  # 関連度低
    EFFORT_TOO_HIGH = "effort_too_high"  # 導入コスト高
    RISK_TOO_HIGH = "risk_too_high"  # リスク高
    ALREADY_COVERED = "already_covered"  # 既に対応済み
    PREMATURE = "premature"  # 時期尚早


@dataclass
class JudgmentDecision:
    """判断結果.

    すべてのIssue/提案に必須。
    """

    item_id: str
    title: str
    status: DecisionStatus
    scores: ScoreBreakdown
    decision_reason: str
    reject_reason: RejectReason | None = None
    reject_detail: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        result = {
            "item_id": self.item_id,
            "title": self.title,
            "status": self.status.value,
            "scores": self.scores.to_dict(),
            "decision_reason": self.decision_reason,
            "timestamp": self.timestamp,
        }
        if self.reject_reason:
            result["reject_reason"] = self.reject_reason.value
            result["reject_detail"] = self.reject_detail
        return result


class DecisionMaker:
    """判断決定器.

    判断ルール（固定）:
    IF (Relevance >= 4 AND Evidence >= 3)
       AND (Effort >= 3)
       AND (Risk >= 3)
    THEN ACCEPT
    ELSE REJECT
    """

    # 閾値（固定）
    THRESHOLDS = {
        "relevance": 4,
        "evidence": 3,
        "effort": 3,
        "risk": 3,
    }

    def decide(self, item_id: str, title: str, scores: ScoreBreakdown) -> JudgmentDecision:
        """
        判断を決定.

        Args:
            item_id: アイテムID
            title: タイトル
            scores: 5軸評価結果

        Returns:
            JudgmentDecision
        """
        # 判断ルール適用
        failures = self._check_thresholds(scores)

        if not failures:
            status = DecisionStatus.ACCEPT
            reason = self._generate_accept_reason(scores)
            reject_reason = None
            reject_detail = None
        else:
            status = DecisionStatus.REJECT
            reject_reason, reject_detail = self._classify_reject(failures, scores)
            reason = f"Rejected: {reject_reason.value}"

        decision = JudgmentDecision(
            item_id=item_id,
            title=title,
            status=status,
            scores=scores,
            decision_reason=reason,
            reject_reason=reject_reason,
            reject_detail=reject_detail,
        )

        logger.info(f"Decision for '{title}': {status.value}")
        return decision

    def _check_thresholds(self, scores: ScoreBreakdown) -> list[str]:
        """閾値チェック."""
        failures = []

        if scores.relevance.score < self.THRESHOLDS["relevance"]:
            failures.append("relevance")
        if scores.evidence.score < self.THRESHOLDS["evidence"]:
            failures.append("evidence")
        if scores.effort.score < self.THRESHOLDS["effort"]:
            failures.append("effort")
        if scores.risk.score < self.THRESHOLDS["risk"]:
            failures.append("risk")

        return failures

    def _classify_reject(
        self, failures: list[str], scores: ScoreBreakdown
    ) -> tuple[RejectReason, str]:
        """Reject理由を分類."""
        # 最も深刻な理由を選択
        if "evidence" in failures:
            return (
                RejectReason.EVIDENCE_INSUFFICIENT,
                f"Evidence score {scores.evidence.score} < {self.THRESHOLDS['evidence']}",
            )
        if "relevance" in failures:
            return (
                RejectReason.RELEVANCE_LOW,
                f"Relevance score {scores.relevance.score} < {self.THRESHOLDS['relevance']}",
            )
        if "effort" in failures:
            return (
                RejectReason.EFFORT_TOO_HIGH,
                f"Effort score {scores.effort.score} < {self.THRESHOLDS['effort']}",
            )
        if "risk" in failures:
            return (
                RejectReason.RISK_TOO_HIGH,
                f"Risk score {scores.risk.score} < {self.THRESHOLDS['risk']}",
            )

        return (RejectReason.PREMATURE, "Does not meet criteria")

    def _generate_accept_reason(self, scores: ScoreBreakdown) -> str:
        """Accept理由を生成."""
        strengths = []

        if scores.relevance.score >= 4:
            strengths.append(f"High relevance ({scores.relevance.score})")
        if scores.evidence.score >= 4:
            strengths.append(f"Strong evidence ({scores.evidence.score})")
        if scores.novelty.score >= 4:
            strengths.append(f"Novel ({scores.novelty.score})")

        if strengths:
            return "Accepted: " + ", ".join(strengths)
        return f"Accepted: Meets all thresholds (avg={scores.average:.1f})"