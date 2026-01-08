"""
JARVIS Quality Gate Verifier

Step 21-40: Verify強制、品質ゲート、fail理由コード化
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FailReason:
    """失敗理由（定型コード）."""
    code: str
    msg: str
    severity: str = "error"  # error, warning, info

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "msg": self.msg,
            "severity": self.severity,
        }


# 失敗理由コード（Step 27）
class FailCodes:
    CITATION_MISSING = "CITATION_MISSING"
    LOCATOR_MISSING = "LOCATOR_MISSING"
    EVIDENCE_WEAK = "EVIDENCE_WEAK"
    ASSERTION_DANGER = "ASSERTION_DANGER"
    PII_DETECTED = "PII_DETECTED"
    FETCH_FAIL = "FETCH_FAIL"
    INDEX_MISSING = "INDEX_MISSING"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    VERIFY_NOT_RUN = "VERIFY_NOT_RUN"


@dataclass
class VerifyResult:
    """Verify結果."""
    gate_passed: bool
    fail_reasons: list[FailReason] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    verified: bool = True  # Verifyが実行されたか

    def to_eval_summary(self, run_id: str) -> dict[str, Any]:
        """eval_summary.json形式に変換."""
        return {
            "run_id": run_id,
            "status": "pass" if self.gate_passed else "fail",
            "gate_passed": self.gate_passed,
            "fail_reasons": [r.to_dict() for r in self.fail_reasons],
            "metrics": self.metrics,
            "verified": self.verified,
        }


class QualityGateVerifier:
    """品質ゲート検証器.
    
    Step 21-40: 品質ゲートを強制
    - citation必須
    - locator必須
    - 断定禁止
    - PII検出
    """

    # 断定の危険パターン（Step 24）
    ASSERTION_PATTERNS = [
        r"(?i)\bis\s+definitely\b",
        r"(?i)\bwill\s+certainly\b",
        r"(?i)\bproven\s+fact\b",
        r"(?i)\babsolutely\b",
        r"(?i)\bundoubtedly\b",
        r"確実に",
        r"間違いなく",
        r"絶対に",
    ]

    # PIIパターン（Step 33）
    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\b\d{3}-\d{3}-\d{4}\b",  # Phone
    ]

    def __init__(
        self,
        require_citations: bool = True,
        require_locators: bool = True,
        min_evidence_coverage: float = 0.5,
    ):
        """初期化."""
        self.require_citations = require_citations
        self.require_locators = require_locators
        self.min_evidence_coverage = min_evidence_coverage

    def verify(
        self,
        answer: str,
        citations: list[dict[str, Any]],
        claims: list[dict[str, Any]] | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> VerifyResult:
        """品質ゲートを検証.
        
        Args:
            answer: 回答テキスト
            citations: 引用リスト
            claims: 主張リスト
            evidence: 根拠リスト
        
        Returns:
            VerifyResult
        """
        fail_reasons = []
        metrics = {}

        # Step 22: citation必須
        if self.require_citations:
            if not citations:
                fail_reasons.append(FailReason(
                    code=FailCodes.CITATION_MISSING,
                    msg="Citations are required but none provided.",
                ))

        metrics["citation_count"] = len(citations)

        # Step 23: locator必須
        if self.require_locators and citations:
            missing_locators = 0
            for cit in citations:
                locator = cit.get("locator", {})
                if not locator or not locator.get("section"):
                    missing_locators += 1

            if missing_locators > 0:
                fail_reasons.append(FailReason(
                    code=FailCodes.LOCATOR_MISSING,
                    msg=f"{missing_locators} citations missing locator information.",
                ))

            metrics["locator_coverage"] = 1.0 - (missing_locators / len(citations)) if citations else 0

        # Step 24: 断定の危険チェック
        assertion_matches = []
        for pattern in self.ASSERTION_PATTERNS:
            matches = re.findall(pattern, answer)
            assertion_matches.extend(matches)

        if assertion_matches:
            fail_reasons.append(FailReason(
                code=FailCodes.ASSERTION_DANGER,
                msg=f"Dangerous assertions detected: {assertion_matches[:3]}",
                severity="warning",
            ))

        metrics["assertion_count"] = len(assertion_matches)

        # Step 33: PII検出
        pii_matches = []
        for pattern in self.PII_PATTERNS:
            matches = re.findall(pattern, answer)
            pii_matches.extend(matches)

        if pii_matches:
            fail_reasons.append(FailReason(
                code=FailCodes.PII_DETECTED,
                msg=f"PII detected in answer: {len(pii_matches)} matches",
            ))

        metrics["pii_count"] = len(pii_matches)

        # Step 32: evidence coverage（claimsとevidenceの紐づけ率）
        if claims and evidence:
            claims_with_evidence = set()
            for ev in evidence:
                claim_id = ev.get("claim_id")
                if claim_id:
                    claims_with_evidence.add(claim_id)

            coverage = len(claims_with_evidence) / len(claims) if claims else 0
            metrics["evidence_coverage"] = coverage

            if coverage < self.min_evidence_coverage:
                fail_reasons.append(FailReason(
                    code=FailCodes.EVIDENCE_WEAK,
                    msg=f"Evidence coverage {coverage:.2f} below threshold {self.min_evidence_coverage}",
                ))

        # Step 26: gate_passedを決定
        # errorレベルの失敗があればfail
        errors = [r for r in fail_reasons if r.severity == "error"]
        gate_passed = len(errors) == 0

        return VerifyResult(
            gate_passed=gate_passed,
            fail_reasons=fail_reasons,
            metrics=metrics,
            verified=True,
        )

    def create_unverified_result(self) -> VerifyResult:
        """Verify未実行の結果を作成（Step 30）."""
        return VerifyResult(
            gate_passed=False,
            fail_reasons=[FailReason(
                code=FailCodes.VERIFY_NOT_RUN,
                msg="Quality gate verification was not executed.",
            )],
            metrics={},
            verified=False,
        )


def format_fail_reasons(reasons: list[FailReason]) -> str:
    """fail理由を人間可読形式にフォーマット（Step 34）."""
    if not reasons:
        return "No issues detected."

    lines = ["Quality Gate Issues:"]
    for r in reasons:
        icon = "❌" if r.severity == "error" else "⚠️"
        lines.append(f"  {icon} [{r.code}] {r.msg}")

    return "\n".join(lines)
