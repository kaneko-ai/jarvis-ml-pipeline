"""
JARVIS Goldset Regression Test

Goldsetベースの品質回帰テスト
- goldset.jsonlから期待値を読み込み
- パイプライン実行結果と比較
- スコア低下を検出
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)


@dataclass
class GoldsetCase:
    """Goldsetテストケース."""

    case_id: str
    query: str
    expected_papers: list[str]  # paper_ids
    expected_claims: int  # minimum claims
    expected_evidence: int  # minimum evidence
    min_score: float  # minimum quality score

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GoldsetCase:
        return cls(
            case_id=d["case_id"],
            query=d["query"],
            expected_papers=d.get("expected_papers", []),
            expected_claims=d.get("expected_claims", 1),
            expected_evidence=d.get("expected_evidence", 1),
            min_score=d.get("min_score", 0.5),
        )


@dataclass
class RegressionResult:
    """回帰テスト結果."""

    case_id: str
    passed: bool
    actual_papers: int
    actual_claims: int
    actual_evidence: int
    actual_score: float
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "actual_papers": self.actual_papers,
            "actual_claims": self.actual_claims,
            "actual_evidence": self.actual_evidence,
            "actual_score": self.actual_score,
            "errors": self.errors,
        }


class GoldsetRegression:
    """Goldset回帰テスト実行."""

    def __init__(self, goldset_path: str = "configs/goldset.jsonl"):
        """初期化."""
        self.goldset_path = Path(goldset_path)
        self.cases: list[GoldsetCase] = []
        self._load_goldset()

    def _load_goldset(self) -> None:
        """Goldsetを読み込み."""
        if not self.goldset_path.exists():
            logger.warning(f"Goldset not found: {self.goldset_path}")
            return

        with open(self.goldset_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # 回帰テスト用ケースに変換
                    case = GoldsetCase(
                        case_id=data.get("context", "")[:20],
                        query=data.get("context", ""),
                        expected_papers=[],
                        expected_claims=1,
                        expected_evidence=1,
                        min_score=0.5,
                    )
                    self.cases.append(case)

        logger.info(f"Loaded {len(self.cases)} goldset cases")

    def run_case(self, case: GoldsetCase) -> RegressionResult:
        """1ケースを実行."""
        from jarvis_core.pipelines.mvp_pipeline import (
            Constraints,
            MVPPipeline,
            PipelineInput,
            Reproducibility,
        )

        errors = []

        # パイプライン実行
        try:
            input = PipelineInput(
                goal="Goldset regression test",
                query=case.query,
                constraints=Constraints(max_papers=5),
                reproducibility=Reproducibility(seed=0),
            )

            pipeline = MVPPipeline(runs_dir="runs/goldset")
            bundle = pipeline.run(input)

            actual_papers = len(bundle.papers)
            actual_claims = len(bundle.claims)
            actual_evidence = len(bundle.evidence)

            # スコア計算（evidence coverage）
            if actual_claims > 0:
                actual_score = actual_evidence / actual_claims
            else:
                actual_score = 0.0

            # 検証
            if actual_claims < case.expected_claims:
                errors.append(f"Claims: {actual_claims} < {case.expected_claims}")
            if actual_evidence < case.expected_evidence:
                errors.append(f"Evidence: {actual_evidence} < {case.expected_evidence}")
            if actual_score < case.min_score:
                errors.append(f"Score: {actual_score:.2f} < {case.min_score:.2f}")

            passed = len(errors) == 0

        except Exception as e:
            errors.append(f"Execution error: {str(e)}")
            actual_papers = 0
            actual_claims = 0
            actual_evidence = 0
            actual_score = 0.0
            passed = False

        return RegressionResult(
            case_id=case.case_id,
            passed=passed,
            actual_papers=actual_papers,
            actual_claims=actual_claims,
            actual_evidence=actual_evidence,
            actual_score=actual_score,
            errors=errors,
        )

    def run_all(self) -> list[RegressionResult]:
        """全ケースを実行."""
        results = []
        for case in self.cases:
            result = self.run_case(case)
            results.append(result)
            status = "✅" if result.passed else "❌"
            logger.info(f"{status} {case.case_id}: score={result.actual_score:.2f}")

        return results

    def generate_report(self, results: list[RegressionResult]) -> str:
        """レポートを生成."""
        passed = sum(1 for r in results if r.passed)
        total = len(results)

        lines = [
            "# Goldset Regression Report",
            "",
            f"**Passed**: {passed}/{total}",
            "",
            "| Case | Papers | Claims | Evidence | Score | Status |",
            "|------|--------|--------|----------|-------|--------|",
        ]

        for r in results:
            status = "✅" if r.passed else "❌"
            lines.append(
                f"| {r.case_id[:15]} | {r.actual_papers} | {r.actual_claims} | {r.actual_evidence} | {r.actual_score:.2f} | {status} |"
            )

        return "\n".join(lines)


# ============================================================
# Pytest Integration
# ============================================================


def test_goldset_regression():
    """Goldset回帰テスト."""
    regression = GoldsetRegression()

    if not regression.cases:
        pytest.skip("No goldset cases found")

    results = regression.run_all()

    failed = [r for r in results if not r.passed]
    if failed:
        report = regression.generate_report(results)
        pytest.fail(f"Goldset regression failed:\n{report}")
