"""
JARVIS Evaluation Module - 品質ゲート

全出力の品質ゲートを適用。
v1.1: hypothesis逃げ禁止、evidence span検証統合
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jarvis_core.contracts.types import Claim, Paper


@dataclass
class QualityGateResult:
    """品質ゲート結果."""

    gate_name: str
    passed: bool
    threshold: float
    actual: float
    message: str


@dataclass
class QualityReport:
    """品質レポート."""

    overall_passed: bool
    gates: list[QualityGateResult] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # 詳細メトリクス
    fact_count: int = 0
    hypothesis_count: int = 0
    fact_provenance_rate: float = 0.0
    hypothesis_provenance_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.overall_passed,
            "gates": [
                {
                    "name": g.gate_name,
                    "passed": g.passed,
                    "threshold": g.threshold,
                    "actual": g.actual,
                    "message": g.message,
                }
                for g in self.gates
            ],
            "recommendations": self.recommendations,
            "metrics": {
                "fact_count": self.fact_count,
                "hypothesis_count": self.hypothesis_count,
                "fact_provenance_rate": self.fact_provenance_rate,
                "hypothesis_provenance_rate": self.hypothesis_provenance_rate,
            },
        }


class QualityGates:
    """
    品質ゲート.

    根拠付け率、再現性、パイプライン完走率を検証。

    v1.1 改定:
    - fact/hypothesisを分離してカウント
    - fact_provenance_rate >= 95% が必須
    - fact_without_evidence == 0 が必須
    - hypothesis_in_main_conclusion == 0（仮説を主要結論に含めない）
    """

    DEFAULT_THRESHOLDS = {
        "fact_provenance_rate": 0.95,
        "facts_without_evidence": 0,
        "hypothesis_in_conclusion": 0,
        "pipeline_completion": 1.0,
        "reproducibility": 0.90,
        "evidence_span_valid_rate": 0.95,
        # 後方互換
        "provenance_rate": 0.95,
    }

    def __init__(self, thresholds: dict[str, float] | None = None):
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}

    def _split_claims_by_type(self, claims: list[Claim]) -> dict[str, list[Claim]]:
        """Claimをtypeで分類."""
        result = {"fact": [], "hypothesis": [], "log": [], "other": []}
        for c in claims:
            claim_type = c.claim_type.lower() if c.claim_type else "other"
            if claim_type in result:
                result[claim_type].append(c)
            else:
                result["other"].append(c)
        return result

    def check_provenance(self, claims: list[Claim]) -> QualityGateResult:
        """
        根拠付け率をチェック（後方互換用）.

        全claims（log除く）の根拠付け率を計算。
        """
        evaluable = [c for c in claims if c.claim_type not in ("log",)]
        if not evaluable:
            return QualityGateResult(
                gate_name="provenance_rate",
                passed=True,
                threshold=self.thresholds["provenance_rate"],
                actual=1.0,
                message="No evaluable claims",
            )

        with_evidence = sum(1 for c in evaluable if c.has_evidence())
        rate = with_evidence / len(evaluable)

        return QualityGateResult(
            gate_name="provenance_rate",
            passed=rate >= self.thresholds["provenance_rate"],
            threshold=self.thresholds["provenance_rate"],
            actual=rate,
            message=f"根拠付け率: {rate:.1%} ({with_evidence}/{len(evaluable)})",
        )

    def check_fact_provenance(self, claims: list[Claim]) -> QualityGateResult:
        """
        事実主張の根拠付け率をチェック.

        factとして出す主張は必ずevidenceが必要。
        """
        split = self._split_claims_by_type(claims)
        facts = split["fact"]

        if not facts:
            return QualityGateResult(
                gate_name="fact_provenance_rate",
                passed=True,
                threshold=self.thresholds["fact_provenance_rate"],
                actual=1.0,
                message="No fact claims",
            )

        with_evidence = sum(1 for c in facts if c.has_evidence())
        rate = with_evidence / len(facts)

        return QualityGateResult(
            gate_name="fact_provenance_rate",
            passed=rate >= self.thresholds["fact_provenance_rate"],
            threshold=self.thresholds["fact_provenance_rate"],
            actual=rate,
            message=f"事実根拠率: {rate:.1%} ({with_evidence}/{len(facts)})",
        )

    def check_facts_without_evidence(self, claims: list[Claim]) -> QualityGateResult:
        """
        根拠なし事実をチェック.

        factなのにevidenceがない主張は0件でなければならない。
        """
        split = self._split_claims_by_type(claims)
        facts = split["fact"]
        facts_without = [c for c in facts if not c.has_evidence()]

        count = len(facts_without)
        threshold = self.thresholds["facts_without_evidence"]

        return QualityGateResult(
            gate_name="facts_without_evidence",
            passed=count <= threshold,
            threshold=threshold,
            actual=float(count),
            message=f"根拠なし事実: {count}件",
        )

    def check_hypothesis_in_conclusion(
        self, claims: list[Claim], main_conclusion_claim_ids: list[str] | None = None
    ) -> QualityGateResult:
        """
        仮説が主要結論に含まれていないかチェック.

        hypothesisは要約の主要結論に含めることを禁止。
        """
        if not main_conclusion_claim_ids:
            # 主要結論が未指定の場合はパス
            return QualityGateResult(
                gate_name="hypothesis_in_conclusion",
                passed=True,
                threshold=0,
                actual=0,
                message="主要結論未指定（スキップ）",
            )

        hypotheses_in_conclusion = []
        for c in claims:
            if c.claim_type == "hypothesis" and c.claim_id in main_conclusion_claim_ids:
                hypotheses_in_conclusion.append(c)

        count = len(hypotheses_in_conclusion)
        threshold = self.thresholds["hypothesis_in_conclusion"]

        return QualityGateResult(
            gate_name="hypothesis_in_conclusion",
            passed=count <= threshold,
            threshold=threshold,
            actual=float(count),
            message=f"結論内仮説: {count}件",
        )

    def check_evidence_span_validity(
        self, claims: list[Claim], doc_store: dict[str, Paper] | None = None
    ) -> QualityGateResult:
        """
        Evidence spanの妥当性をチェック.

        EvidenceValidatorを使用してspan検証。
        """
        from jarvis_core.evaluation.evidence_validator import get_evidence_validator

        evaluable = [c for c in claims if c.claim_type == "fact" and c.has_evidence()]

        if not evaluable:
            return QualityGateResult(
                gate_name="evidence_span_valid_rate",
                passed=True,
                threshold=self.thresholds["evidence_span_valid_rate"],
                actual=1.0,
                message="No evidence spans to validate",
            )

        validator = get_evidence_validator(doc_store or {})
        result = validator.validate_all_claims(evaluable, doc_store)
        rate = result["rate"]

        return QualityGateResult(
            gate_name="evidence_span_valid_rate",
            passed=rate >= self.thresholds["evidence_span_valid_rate"],
            threshold=self.thresholds["evidence_span_valid_rate"],
            actual=rate,
            message=f"スパン妥当性: {rate:.1%} ({result['valid']}/{result['total']})",
        )

    def check_pipeline_completion(
        self, expected_stages: int, completed_stages: int
    ) -> QualityGateResult:
        """パイプライン完走率をチェック."""
        rate = completed_stages / expected_stages if expected_stages > 0 else 0
        threshold = self.thresholds["pipeline_completion"]

        return QualityGateResult(
            gate_name="pipeline_completion",
            passed=rate >= threshold,
            threshold=threshold,
            actual=rate,
            message=f"完走率: {rate:.1%} ({completed_stages}/{expected_stages})",
        )

    def check_reproducibility(
        self, baseline_top10: list[str], current_top10: list[str]
    ) -> QualityGateResult:
        """再現性（Top10一致率）をチェック."""
        if not baseline_top10 or not current_top10:
            return QualityGateResult(
                gate_name="reproducibility",
                passed=True,  # No baseline to compare
                threshold=self.thresholds["reproducibility"],
                actual=1.0,
                message="ベースラインなし（スキップ）",
            )

        matches = sum(1 for item in current_top10 if item in baseline_top10)
        rate = matches / len(baseline_top10)
        threshold = self.thresholds["reproducibility"]

        return QualityGateResult(
            gate_name="reproducibility",
            passed=rate >= threshold,
            threshold=threshold,
            actual=rate,
            message=f"Top10一致率: {rate:.1%} ({matches}/10)",
        )

    def run_all(
        self,
        claims: list[Claim],
        expected_stages: int = 10,
        completed_stages: int = 10,
        baseline_top10: list[str] | None = None,
        current_top10: list[str] | None = None,
        main_conclusion_claim_ids: list[str] | None = None,
        doc_store: dict[str, Paper] | None = None,
        validate_evidence_spans: bool = True,
    ) -> QualityReport:
        """
        全ゲートを実行.

        v1.1: fact/hypothesis分離、evidence span検証追加
        """
        split = self._split_claims_by_type(claims)

        gates = [
            self.check_fact_provenance(claims),
            self.check_facts_without_evidence(claims),
            self.check_hypothesis_in_conclusion(claims, main_conclusion_claim_ids),
            self.check_pipeline_completion(expected_stages, completed_stages),
        ]

        # Evidence span検証（オプション）
        if validate_evidence_spans:
            gates.append(self.check_evidence_span_validity(claims, doc_store))

        # 再現性チェック
        if baseline_top10 and current_top10:
            gates.append(self.check_reproducibility(baseline_top10, current_top10))

        overall_passed = all(g.passed for g in gates)

        recommendations = []
        for g in gates:
            if not g.passed:
                recommendations.append(self._get_recommendation(g.gate_name))

        # メトリクス計算
        facts = split["fact"]
        hypotheses = split["hypothesis"]
        fact_with_ev = sum(1 for c in facts if c.has_evidence())
        hyp_with_ev = sum(1 for c in hypotheses if c.has_evidence())

        return QualityReport(
            overall_passed=overall_passed,
            gates=gates,
            recommendations=recommendations,
            fact_count=len(facts),
            hypothesis_count=len(hypotheses),
            fact_provenance_rate=fact_with_ev / len(facts) if facts else 0.0,
            hypothesis_provenance_rate=hyp_with_ev / len(hypotheses) if hypotheses else 0.0,
        )

    def _get_recommendation(self, gate_name: str) -> str:
        """推奨対応を取得."""
        recs = {
            "provenance_rate": "根拠のない主張を削除するか、証拠を追加してください",
            "fact_provenance_rate": "事実主張には必ず証拠を付与してください",
            "facts_without_evidence": "事実として主張する場合は必ず証拠を付与してください",
            "hypothesis_in_conclusion": "仮説は主要結論から除外し、別セクションに隔離してください",
            "evidence_span_valid_rate": "証拠スパンが正しい原文範囲を参照しているか確認してください",
            "pipeline_completion": "失敗したステージのログを確認してください",
            "reproducibility": "シードを固定し、決定的な処理を使用してください",
        }
        return recs.get(gate_name, "")


def get_quality_gates(thresholds: dict[str, float] | None = None) -> QualityGates:
    """品質ゲートを取得."""
    return QualityGates(thresholds)