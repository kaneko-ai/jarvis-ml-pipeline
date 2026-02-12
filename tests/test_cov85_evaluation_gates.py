"""Coverage tests for jarvis_core.evaluation.gates."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis_core.evaluation.gates import (
    QualityGateResult,
    QualityGates,
    QualityReport,
    get_quality_gates,
)


def _make_claim(claim_id="c1", claim_type="fact", has_ev=True):
    c = MagicMock()
    c.claim_id = claim_id
    c.claim_type = claim_type
    c.has_evidence.return_value = has_ev
    return c


class TestQualityGateResult:
    def test_basic(self) -> None:
        r = QualityGateResult(
            gate_name="test", passed=True, threshold=0.9, actual=1.0, message="ok"
        )
        assert r.passed is True


class TestQualityReport:
    def test_to_dict(self) -> None:
        gate = QualityGateResult(
            gate_name="g1", passed=True, threshold=0.9, actual=0.95, message="ok"
        )
        report = QualityReport(
            overall_passed=True,
            gates=[gate],
            recommendations=["rec1"],
            fact_count=5,
            hypothesis_count=2,
            fact_provenance_rate=0.95,
            hypothesis_provenance_rate=0.5,
        )
        d = report.to_dict()
        assert d["passed"] is True
        assert len(d["gates"]) == 1
        assert d["metrics"]["fact_count"] == 5


class TestQualityGates:
    def test_init_defaults(self) -> None:
        gates = QualityGates()
        assert gates.thresholds["fact_provenance_rate"] == 0.95

    def test_init_custom(self) -> None:
        gates = QualityGates(thresholds={"fact_provenance_rate": 0.8})
        assert gates.thresholds["fact_provenance_rate"] == 0.8

    def test_split_claims_by_type(self) -> None:
        gates = QualityGates()
        claims = [
            _make_claim("c1", "fact"),
            _make_claim("c2", "hypothesis"),
            _make_claim("c3", "log"),
            _make_claim("c4", "custom_type"),
        ]
        result = gates._split_claims_by_type(claims)
        assert len(result["fact"]) == 1
        assert len(result["hypothesis"]) == 1
        assert len(result["log"]) == 1
        assert len(result["other"]) == 1

    def test_check_provenance_no_claims(self) -> None:
        gates = QualityGates()
        result = gates.check_provenance([])
        assert result.passed is True

    def test_check_provenance_all_evidenced(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True), _make_claim("c2", "fact", True)]
        result = gates.check_provenance(claims)
        assert result.passed is True
        assert result.actual == 1.0

    def test_check_provenance_some_missing(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True), _make_claim("c2", "fact", False)]
        result = gates.check_provenance(claims)
        assert result.actual == 0.5

    def test_check_provenance_log_excluded(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "log", False)]
        result = gates.check_provenance(claims)
        assert result.passed is True

    def test_check_fact_provenance_no_facts(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "hypothesis")]
        result = gates.check_fact_provenance(claims)
        assert result.passed is True

    def test_check_fact_provenance_pass(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True)]
        result = gates.check_fact_provenance(claims)
        assert result.passed is True

    def test_check_fact_provenance_fail(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", False)]
        result = gates.check_fact_provenance(claims)
        assert result.passed is False

    def test_check_facts_without_evidence(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", False)]
        result = gates.check_facts_without_evidence(claims)
        assert result.passed is False
        assert result.actual == 1.0

    def test_check_facts_without_evidence_ok(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True)]
        result = gates.check_facts_without_evidence(claims)
        assert result.passed is True

    def test_check_hypothesis_in_conclusion_no_ids(self) -> None:
        gates = QualityGates()
        result = gates.check_hypothesis_in_conclusion([], None)
        assert result.passed is True

    def test_check_hypothesis_in_conclusion_found(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "hypothesis")]
        result = gates.check_hypothesis_in_conclusion(claims, ["c1"])
        assert result.passed is False

    def test_check_hypothesis_in_conclusion_not_found(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact")]
        result = gates.check_hypothesis_in_conclusion(claims, ["c1"])
        assert result.passed is True

    def test_check_evidence_span_validity_no_evaluable(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "hypothesis")]
        result = gates.check_evidence_span_validity(claims)
        assert result.passed is True

    def test_check_evidence_span_validity_with_claims(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True)]

        mock_validator = MagicMock()
        mock_validator.validate_all_claims.return_value = {"rate": 1.0, "valid": 1, "total": 1}

        with patch(
            "jarvis_core.evaluation.evidence_validator.get_evidence_validator",
            return_value=mock_validator,
        ):
            result = gates.check_evidence_span_validity(claims)
        assert result.passed is True

    def test_check_pipeline_completion_pass(self) -> None:
        gates = QualityGates()
        result = gates.check_pipeline_completion(10, 10)
        assert result.passed is True

    def test_check_pipeline_completion_fail(self) -> None:
        gates = QualityGates()
        result = gates.check_pipeline_completion(10, 5)
        assert result.passed is False

    def test_check_pipeline_completion_zero(self) -> None:
        gates = QualityGates()
        result = gates.check_pipeline_completion(0, 0)
        assert result.passed is False

    def test_check_reproducibility_no_baseline(self) -> None:
        gates = QualityGates()
        result = gates.check_reproducibility([], ["a"])
        assert result.passed is True

    def test_check_reproducibility_pass(self) -> None:
        gates = QualityGates()
        baseline = [f"p{i}" for i in range(10)]
        current = [f"p{i}" for i in range(10)]
        result = gates.check_reproducibility(baseline, current)
        assert result.passed is True

    def test_check_reproducibility_fail(self) -> None:
        gates = QualityGates()
        baseline = [f"p{i}" for i in range(10)]
        current = [f"x{i}" for i in range(10)]
        result = gates.check_reproducibility(baseline, current)
        assert result.passed is False

    def test_run_all_all_pass(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True)]

        mock_validator = MagicMock()
        mock_validator.validate_all_claims.return_value = {"rate": 1.0, "valid": 1, "total": 1}

        with patch(
            "jarvis_core.evaluation.evidence_validator.get_evidence_validator",
            return_value=mock_validator,
        ):
            report = gates.run_all(claims)
        assert report.overall_passed is True
        assert report.fact_count == 1

    def test_run_all_with_reproducibility(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True)]
        baseline = ["p1", "p2"]
        current = ["p1", "p2"]

        mock_validator = MagicMock()
        mock_validator.validate_all_claims.return_value = {"rate": 1.0, "valid": 1, "total": 1}

        with patch(
            "jarvis_core.evaluation.evidence_validator.get_evidence_validator",
            return_value=mock_validator,
        ):
            report = gates.run_all(
                claims,
                baseline_top10=baseline,
                current_top10=current,
            )
        assert report.overall_passed is True

    def test_run_all_failed_gate_gives_recommendation(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", False)]

        with patch(
            "jarvis_core.evaluation.evidence_validator.get_evidence_validator",
            return_value=MagicMock(
                validate_all_claims=MagicMock(return_value={"rate": 0, "valid": 0, "total": 0})
            ),
        ):
            report = gates.run_all(claims, validate_evidence_spans=False)
        assert report.overall_passed is False
        assert len(report.recommendations) > 0

    def test_run_all_no_evidence_spans(self) -> None:
        gates = QualityGates()
        claims = [_make_claim("c1", "fact", True)]
        report = gates.run_all(claims, validate_evidence_spans=False)
        assert report.overall_passed is True

    def test_get_recommendation(self) -> None:
        gates = QualityGates()
        rec = gates._get_recommendation("fact_provenance_rate")
        assert "証拠" in rec
        assert gates._get_recommendation("nonexistent") == ""


class TestGetQualityGates:
    def test_factory(self) -> None:
        gates = get_quality_gates()
        assert isinstance(gates, QualityGates)
        assert gates.thresholds["fact_provenance_rate"] == 0.95
        assert gates.thresholds["pipeline_completion"] == 1.0

    def test_factory_with_thresholds(self) -> None:
        gates = get_quality_gates({"fact_provenance_rate": 0.5})
        assert gates.thresholds["fact_provenance_rate"] == 0.5
