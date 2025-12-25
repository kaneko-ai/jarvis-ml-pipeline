"""
JARVIS Evaluation Module - 品質ゲート

全出力の品質ゲートを適用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis_core.contracts.types import Claim, ResultBundle


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
    gates: List[QualityGateResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.overall_passed,
            "gates": [
                {"name": g.gate_name, "passed": g.passed, 
                 "threshold": g.threshold, "actual": g.actual, "message": g.message}
                for g in self.gates
            ],
            "recommendations": self.recommendations
        }


class QualityGates:
    """
    品質ゲート.
    
    根拠付け率、再現性、パイプライン完走率を検証。
    """
    
    DEFAULT_THRESHOLDS = {
        "provenance_rate": 0.95,
        "facts_without_evidence": 0,
        "pipeline_completion": 1.0,
        "reproducibility": 0.90
    }
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
    
    def check_provenance(self, claims: List[Claim]) -> QualityGateResult:
        """根拠付け率をチェック."""
        if not claims:
            return QualityGateResult(
                gate_name="provenance_rate",
                passed=False,
                threshold=self.thresholds["provenance_rate"],
                actual=0.0,
                message="No claims to evaluate"
            )
        
        with_evidence = sum(1 for c in claims if c.has_evidence())
        rate = with_evidence / len(claims)
        
        return QualityGateResult(
            gate_name="provenance_rate",
            passed=rate >= self.thresholds["provenance_rate"],
            threshold=self.thresholds["provenance_rate"],
            actual=rate,
            message=f"根拠付け率: {rate:.1%} ({with_evidence}/{len(claims)})"
        )
    
    def check_facts_without_evidence(self, claims: List[Claim]) -> QualityGateResult:
        """根拠なし事実をチェック."""
        facts = [c for c in claims if c.claim_type == "fact"]
        facts_without = [c for c in facts if not c.has_evidence()]
        
        count = len(facts_without)
        threshold = self.thresholds["facts_without_evidence"]
        
        return QualityGateResult(
            gate_name="facts_without_evidence",
            passed=count <= threshold,
            threshold=threshold,
            actual=float(count),
            message=f"根拠なし事実: {count}件"
        )
    
    def check_pipeline_completion(self, 
                                  expected_stages: int, 
                                  completed_stages: int) -> QualityGateResult:
        """パイプライン完走率をチェック."""
        rate = completed_stages / expected_stages if expected_stages > 0 else 0
        threshold = self.thresholds["pipeline_completion"]
        
        return QualityGateResult(
            gate_name="pipeline_completion",
            passed=rate >= threshold,
            threshold=threshold,
            actual=rate,
            message=f"完走率: {rate:.1%} ({completed_stages}/{expected_stages})"
        )
    
    def check_reproducibility(self, 
                              baseline_top10: List[str], 
                              current_top10: List[str]) -> QualityGateResult:
        """再現性（Top10一致率）をチェック."""
        if not baseline_top10 or not current_top10:
            return QualityGateResult(
                gate_name="reproducibility",
                passed=True,  # No baseline to compare
                threshold=self.thresholds["reproducibility"],
                actual=1.0,
                message="ベースラインなし（スキップ）"
            )
        
        matches = sum(1 for item in current_top10 if item in baseline_top10)
        rate = matches / len(baseline_top10)
        threshold = self.thresholds["reproducibility"]
        
        return QualityGateResult(
            gate_name="reproducibility",
            passed=rate >= threshold,
            threshold=threshold,
            actual=rate,
            message=f"Top10一致率: {rate:.1%} ({matches}/10)"
        )
    
    def run_all(self, 
                claims: List[Claim],
                expected_stages: int = 10,
                completed_stages: int = 10,
                baseline_top10: Optional[List[str]] = None,
                current_top10: Optional[List[str]] = None) -> QualityReport:
        """全ゲートを実行."""
        gates = [
            self.check_provenance(claims),
            self.check_facts_without_evidence(claims),
            self.check_pipeline_completion(expected_stages, completed_stages)
        ]
        
        if baseline_top10 and current_top10:
            gates.append(self.check_reproducibility(baseline_top10, current_top10))
        
        overall_passed = all(g.passed for g in gates)
        
        recommendations = []
        for g in gates:
            if not g.passed:
                recommendations.append(self._get_recommendation(g.gate_name))
        
        return QualityReport(
            overall_passed=overall_passed,
            gates=gates,
            recommendations=recommendations
        )
    
    def _get_recommendation(self, gate_name: str) -> str:
        """推奨対応を取得."""
        recs = {
            "provenance_rate": "根拠のない主張を削除するか、証拠を追加してください",
            "facts_without_evidence": "事実として主張する場合は必ず証拠を付与してください",
            "pipeline_completion": "失敗したステージのログを確認してください",
            "reproducibility": "シードを固定し、決定的な処理を使用してください"
        }
        return recs.get(gate_name, "")


def get_quality_gates(thresholds: Optional[Dict[str, float]] = None) -> QualityGates:
    """品質ゲートを取得."""
    return QualityGates(thresholds)
