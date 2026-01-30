"""Judge - 二系統化.

Phase Loop 3: Judge二系統化
- Judge-A: 形式チェック（citation/構造）
- Judge-B: 意味整合チェック（粗くてよい）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class JudgeType(Enum):
    """Judge種別."""

    FORM = "form"  # 形式チェック (Judge-A)
    SEMANTIC = "semantic"  # 意味整合チェック (Judge-B)


@dataclass
class JudgeResult:
    """Judge結果."""

    judge_type: JudgeType
    passed: bool
    issues: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class FormJudge:
    """Judge-A: 形式チェック.

    チェック項目:
    - citation存在
    - citation構造（必須フィールド）
    - locator存在
    - 結果構造
    """

    REQUIRED_CITATION_FIELDS = {"paper_id"}
    REQUIRED_LOCATOR_FIELDS = {"section"}

    def judge(
        self,
        answer: str,
        citations: list[dict[str, Any]],
        result: dict[str, Any] | None = None,
    ) -> JudgeResult:
        """形式をチェック.

        Args:
            answer: 回答
            citations: 引用リスト
            result: 結果全体（オプション）

        Returns:
            JudgeResult
        """
        issues = []
        checks_passed = 0
        total_checks = 0

        # 1. Citation存在チェック
        total_checks += 1
        if citations:
            checks_passed += 1
        else:
            issues.append(
                {
                    "check": "citation_exists",
                    "passed": False,
                    "msg": "No citations provided",
                }
            )

        # 2. Citation構造チェック
        if citations:
            for i, cit in enumerate(citations):
                total_checks += 1
                missing = self.REQUIRED_CITATION_FIELDS - set(cit.keys())
                if not missing:
                    checks_passed += 1
                else:
                    issues.append(
                        {
                            "check": "citation_structure",
                            "passed": False,
                            "index": i,
                            "missing": list(missing),
                        }
                    )

        # 3. Locator存在チェック
        for i, cit in enumerate(citations):
            total_checks += 1
            locator = cit.get("locator", {})
            if locator and self.REQUIRED_LOCATOR_FIELDS.issubset(set(locator.keys())):
                checks_passed += 1
            else:
                issues.append(
                    {
                        "check": "locator_exists",
                        "passed": False,
                        "index": i,
                        "msg": "Missing or incomplete locator",
                    }
                )

        # 4. Answer存在チェック
        total_checks += 1
        if answer and len(answer.strip()) > 0:
            checks_passed += 1
        else:
            issues.append(
                {
                    "check": "answer_exists",
                    "passed": False,
                    "msg": "Answer is empty",
                }
            )

        score = checks_passed / total_checks if total_checks > 0 else 0.0
        passed = len([i for i in issues if not i.get("passed", True)]) == 0

        return JudgeResult(
            judge_type=JudgeType.FORM,
            passed=passed,
            issues=issues,
            score=score,
            details={
                "checks_passed": checks_passed,
                "total_checks": total_checks,
            },
        )


class SemanticJudge:
    """Judge-B: 意味整合チェック.

    チェック項目（粗い実装）:
    - 回答と引用の関連性（キーワード重複）
    - 論理的一貫性（簡易）
    """

    def judge(
        self,
        answer: str,
        citations: list[dict[str, Any]],
        claims: list[dict[str, Any]] | None = None,
    ) -> JudgeResult:
        """意味整合をチェック.

        Args:
            answer: 回答
            citations: 引用リスト
            claims: 主張リスト（オプション）

        Returns:
            JudgeResult
        """
        issues = []
        checks_passed = 0
        total_checks = 0

        # 1. 回答と引用のキーワード重複チェック（簡易）
        total_checks += 1
        answer_words = set(answer.lower().split())

        citation_overlap = 0
        for cit in citations:
            evidence_text = cit.get("evidence_text", "")
            if evidence_text:
                evidence_words = set(evidence_text.lower().split())
                overlap = len(answer_words & evidence_words)
                if overlap > 0:
                    citation_overlap += 1

        if citation_overlap > 0 or not citations:
            checks_passed += 1
        else:
            issues.append(
                {
                    "check": "answer_citation_relevance",
                    "passed": False,
                    "msg": "Answer may not be related to citations",
                }
            )

        # 2. 長さの妥当性チェック
        total_checks += 1
        if len(answer) >= 10:  # 最低10文字
            checks_passed += 1
        else:
            issues.append(
                {
                    "check": "answer_length",
                    "passed": False,
                    "msg": "Answer is too short",
                }
            )

        # 3. 主張との整合性（claimsがある場合）
        if claims:
            total_checks += 1
            # 簡易: 少なくとも1つのclaimが回答に含まれているか
            claim_found = False
            for claim in claims:
                claim_text = claim.get("claim_text", "")
                if claim_text and any(
                    word in answer.lower() for word in claim_text.lower().split()[:3]
                ):
                    claim_found = True
                    break

            if claim_found:
                checks_passed += 1
            else:
                issues.append(
                    {
                        "check": "claim_consistency",
                        "passed": False,
                        "msg": "Answer may not reflect extracted claims",
                    }
                )

        score = checks_passed / total_checks if total_checks > 0 else 0.0
        passed = score >= 0.5  # 50%以上でpass

        return JudgeResult(
            judge_type=JudgeType.SEMANTIC,
            passed=passed,
            issues=issues,
            score=score,
            details={
                "checks_passed": checks_passed,
                "total_checks": total_checks,
            },
        )


class IntegratedJudge:
    """統合Judge.

    Judge-AとJudge-Bの結果を統合。
    """

    def __init__(self):
        self.form_judge = FormJudge()
        self.semantic_judge = SemanticJudge()

    def judge(
        self,
        answer: str,
        citations: list[dict[str, Any]],
        claims: list[dict[str, Any]] | None = None,
        result: dict[str, Any] | None = None,
    ) -> dict[str, JudgeResult]:
        """統合判定.

        Returns:
            {"form": JudgeResult, "semantic": JudgeResult}
        """
        form_result = self.form_judge.judge(answer, citations, result)
        semantic_result = self.semantic_judge.judge(answer, citations, claims)

        return {
            "form": form_result,
            "semantic": semantic_result,
        }

    def overall_passed(
        self,
        answer: str,
        citations: list[dict[str, Any]],
        claims: list[dict[str, Any]] | None = None,
    ) -> bool:
        """総合判定.

        規約: 両方passで成功（部分成功はsuccessにしない）
        """
        results = self.judge(answer, citations, claims)
        return results["form"].passed and results["semantic"].passed
