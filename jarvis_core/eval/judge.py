"""
JARVIS Judge & Retry

Step 61-80: Judge/再試行、自動品質改善
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetryAttempt:
    """再試行記録（Step 62）."""

    attempt: int
    changes_made: list[str]
    result_improved: bool
    cost: float
    time_ms: int
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "changes_made": self.changes_made,
            "result_improved": self.result_improved,
            "cost": self.cost,
            "time_ms": self.time_ms,
            "timestamp": self.timestamp,
        }


@dataclass
class JudgeResult:
    """Judge結果."""

    passed: bool
    format_score: float  # 形式チェック
    citation_score: float  # 引用整合
    overall_score: float
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "format_score": self.format_score,
            "citation_score": self.citation_score,
            "overall_score": self.overall_score,
            "issues": self.issues,
        }


# 再試行戦略（Step 61）
RETRY_STRATEGIES = {
    "CITATION_MISSING": {
        "action": "add_search",
        "description": "Add additional paper search to find citations",
    },
    "LOCATOR_MISSING": {
        "action": "extract_locators",
        "description": "Re-extract evidence with locator information",
    },
    "EVIDENCE_WEAK": {
        "action": "expand_search",
        "description": "Expand search to find more supporting evidence",
    },
    "ASSERTION_DANGER": {
        "action": "soften_language",
        "description": "Rewrite with hedging language",
    },
}


class Judge:
    """2系統Judge（Step 66）.

    - 形式チェック（構造、必須フィールド）
    - 引用整合チェック（引用元と主張の関連性）
    """

    def __init__(
        self,
        format_threshold: float = 0.7,
        citation_threshold: float = 0.6,
    ):
        """初期化."""
        self.format_threshold = format_threshold
        self.citation_threshold = citation_threshold

    def judge(
        self,
        result: dict[str, Any],
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> JudgeResult:
        """2系統Judgeを実行."""
        issues = []

        # 形式チェック
        format_score = self._check_format(result, claims, evidence)
        if format_score < self.format_threshold:
            issues.append(f"Format score {format_score:.2f} below threshold")

        # 引用整合チェック
        citation_score = self._check_citation_coherence(claims, evidence)
        if citation_score < self.citation_threshold:
            issues.append(f"Citation coherence {citation_score:.2f} below threshold")

        # 総合スコア
        overall_score = (format_score + citation_score) / 2
        passed = format_score >= self.format_threshold and citation_score >= self.citation_threshold

        return JudgeResult(
            passed=passed,
            format_score=format_score,
            citation_score=citation_score,
            overall_score=overall_score,
            issues=issues,
        )

    def _check_format(
        self,
        result: dict[str, Any],
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> float:
        """形式チェック."""
        score = 1.0

        # 必須フィールド
        if not result.get("answer"):
            score -= 0.3
        if not result.get("citations"):
            score -= 0.3
        if not claims:
            score -= 0.2
        if not evidence:
            score -= 0.2

        return max(0.0, score)

    def _check_citation_coherence(
        self,
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> float:
        """引用整合チェック（Step 32）."""
        if not claims:
            return 0.0

        # evidenceがあるclaimの割合
        evidence_claim_ids = {e.get("claim_id") for e in evidence if e.get("claim_id")}
        claims_with_evidence = sum(1 for c in claims if c.get("claim_id") in evidence_claim_ids)

        return claims_with_evidence / len(claims)


class RetryManager:
    """再試行マネージャー.

    Step 61-74: 自動リトライ
    """

    def __init__(
        self,
        max_retries: int = 3,
        cost_limit: float = 10.0,
    ):
        """初期化."""
        self.max_retries = max_retries
        self.cost_limit = cost_limit
        self.attempts: list[RetryAttempt] = []
        self.total_cost = 0.0

    def should_retry(
        self,
        fail_codes: list[str],
        current_attempt: int,
    ) -> bool:
        """再試行すべきか判定（Step 63, 69）."""
        # 回数上限
        if current_attempt >= self.max_retries:
            logger.info(f"Max retries ({self.max_retries}) reached")
            return False

        # コスト上限
        if self.total_cost >= self.cost_limit:
            logger.info(f"Cost limit ({self.cost_limit}) reached")
            return False

        # 再試行可能なエラーがあるか
        retryable = any(code in RETRY_STRATEGIES for code in fail_codes)
        return retryable

    def get_retry_strategy(self, fail_codes: list[str]) -> list[dict[str, Any]]:
        """再試行戦略を取得（Step 61）."""
        strategies = []
        for code in fail_codes:
            if code in RETRY_STRATEGIES:
                strategies.append(
                    {
                        "code": code,
                        **RETRY_STRATEGIES[code],
                    }
                )
        return strategies

    def record_attempt(
        self,
        attempt: int,
        changes: list[str],
        improved: bool,
        cost: float,
        time_ms: int,
    ) -> None:
        """試行を記録（Step 62, 64, 65）."""
        self.attempts.append(
            RetryAttempt(
                attempt=attempt,
                changes_made=changes,
                result_improved=improved,
                cost=cost,
                time_ms=time_ms,
                timestamp=datetime.now().isoformat(),
            )
        )
        self.total_cost += cost

    def get_summary(self) -> dict[str, Any]:
        """サマリーを取得（Step 74）."""
        return {
            "total_attempts": len(self.attempts),
            "total_cost": self.total_cost,
            "attempts": [a.to_dict() for a in self.attempts],
            "any_improved": any(a.result_improved for a in self.attempts),
        }


# 評価指標（Step 75-77）
class EvalMetrics:
    """評価指標."""

    THRESHOLDS = {
        "citation_count": 1,  # 最低1件
        "evidence_coverage": 0.5,  # 50%以上
        "locator_coverage": 0.8,  # 80%以上
        "format_score": 0.7,
        "citation_score": 0.6,
    }

    @classmethod
    def check_thresholds(cls, metrics: dict[str, Any]) -> list[str]:
        """閾値チェック（Step 79）."""
        violations = []
        for key, threshold in cls.THRESHOLDS.items():
            value = metrics.get(key)
            if value is not None and value < threshold:
                violations.append(f"{key}: {value} < {threshold}")
        return violations