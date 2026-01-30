"""Comprehensive tests for jarvis_core.decision module.

Tests for:
- schema.py: Pydantic models and validators
- model.py: evaluate_options function
- elicitation.py: template_payload, validate_payload, normalize_risks
- simulator.py: sample_distribution, simulate_option, helper functions
- planner.py: assess_plan_time, PlanTimeAssessment
- risk_factors.py: RiskFactorDefinition, default_risk_inputs
"""

import pytest
from unittest.mock import patch
import random


# ============================================================
# Tests for schema.py
# ============================================================


class TestRationaleValue:
    """Tests for RationaleValue model."""

    def test_valid_rationale_value(self):
        from jarvis_core.decision.schema import RationaleValue

        rv = RationaleValue(value=0.5, rationale="Test rationale")
        assert rv.value == 0.5
        assert rv.rationale == "Test rationale"

    def test_empty_rationale_raises_error(self):
        from jarvis_core.decision.schema import RationaleValue

        with pytest.raises(ValueError, match="rationale"):
            RationaleValue(value=0.5, rationale="   ")

    def test_missing_rationale_raises_error(self):
        from jarvis_core.decision.schema import RationaleValue
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RationaleValue(value=0.5)


class TestDistributions:
    """Tests for distribution models."""

    def test_triangular_distribution(self):
        from jarvis_core.decision.schema import TriangularDistribution, RationaleValue

        low = RationaleValue(value=1.0, rationale="min")
        mode = RationaleValue(value=2.0, rationale="mode")
        high = RationaleValue(value=3.0, rationale="max")
        dist = TriangularDistribution(type="triangular", low=low, mode=mode, high=high)
        assert dist.type == "triangular"
        assert dist.unit == "months"

    def test_normal_distribution(self):
        from jarvis_core.decision.schema import NormalDistribution, RationaleValue

        mean = RationaleValue(value=5.0, rationale="mean")
        std = RationaleValue(value=1.0, rationale="std")
        dist = NormalDistribution(type="normal", mean=mean, std=std, unit="weeks")
        assert dist.type == "normal"
        assert dist.unit == "weeks"

    def test_lognormal_distribution(self):
        from jarvis_core.decision.schema import LogNormalDistribution, RationaleValue

        mean = RationaleValue(value=2.0, rationale="mean")
        sigma = RationaleValue(value=0.5, rationale="sigma")
        dist = LogNormalDistribution(type="lognormal", mean=mean, sigma=sigma)
        assert dist.type == "lognormal"


class TestAssumption:
    """Tests for Assumption model."""

    def test_assumption_creation(self):
        from jarvis_core.decision.schema import (
            Assumption,
            TriangularDistribution,
            RationaleValue,
        )

        dist = TriangularDistribution(
            type="triangular",
            low=RationaleValue(value=1.0, rationale="min"),
            mode=RationaleValue(value=2.0, rationale="mode"),
            high=RationaleValue(value=4.0, rationale="max"),
        )
        assumption = Assumption(
            assumption_id="A1",
            name="Test Assumption",
            distribution=dist,
            rationale="Test rationale for assumption",
            applies_to="setup",
        )
        assert assumption.assumption_id == "A1"
        assert assumption.applies_to == "setup"


class TestConstraintsAndDependencies:
    """Tests for Constraints and Dependencies models."""

    def test_constraints_creation(self):
        from jarvis_core.decision.schema import Constraints, RationaleValue

        constraints = Constraints(
            weekly_hours=RationaleValue(value=40.0, rationale="standard work week"),
            budget_level="medium",
            equipment_access="high",
            mentor_support="moderate",
        )
        assert constraints.budget_level == "medium"

    def test_dependencies_creation(self):
        from jarvis_core.decision.schema import Dependencies

        deps = Dependencies(
            must_learn=["python", "ml"],
            must_access=["gpu cluster"],
        )
        assert len(deps.must_learn) == 2
        assert "gpu cluster" in deps.must_access

    def test_dependencies_defaults(self):
        from jarvis_core.decision.schema import Dependencies

        deps = Dependencies()
        assert deps.must_learn == []
        assert deps.must_access == []


class TestRiskFactorInput:
    """Tests for RiskFactorInput model."""

    def test_risk_factor_input(self):
        from jarvis_core.decision.schema import RiskFactorInput, RationaleValue

        risk = RiskFactorInput(
            name="Technical Risk",
            score=RationaleValue(value=0.7, rationale="high complexity"),
            weight=RationaleValue(value=1.5, rationale="important factor"),
            rationale="Technology is unproven",
        )
        assert risk.name == "Technical Risk"
        assert risk.score.value == 0.7


class TestOption:
    """Tests for Option model."""

    def test_option_creation(self):
        from jarvis_core.decision.schema import (
            Option,
            Constraints,
            Dependencies,
            RationaleValue,
        )

        option = Option(
            option_id="O1",
            label="Test Option",
            goal="Achieve something",
            theme="Research",
            time_horizon_months=RationaleValue(value=24.0, rationale="2 years"),
            constraints=Constraints(
                weekly_hours=RationaleValue(value=40.0, rationale="full-time"),
                budget_level="high",
                equipment_access="medium",
                mentor_support="high",
            ),
            dependencies=Dependencies(must_learn=["skill1"], must_access=["resource1"]),
        )
        assert option.option_id == "O1"
        assert option.time_horizon_months.value == 24.0


class TestDecisionInput:
    """Tests for DecisionInput model."""

    def test_decision_input_empty(self):
        from jarvis_core.decision.schema import DecisionInput

        di = DecisionInput(options=[], assumptions=[])
        assert len(di.options) == 0
        assert di.user_constraints is None


class TestOutputModels:
    """Tests for output-related models."""

    def test_probability_range(self):
        from jarvis_core.decision.schema import ProbabilityRange

        pr = ProbabilityRange(p10=0.2, p50=0.5, p90=0.8)
        assert pr.p10 < pr.p50 < pr.p90

    def test_expected_outputs(self):
        from jarvis_core.decision.schema import ExpectedOutputs, ProbabilityRange

        papers = ProbabilityRange(p10=1.0, p50=2.0, p90=4.0)
        presentations = ProbabilityRange(p10=2.0, p50=4.0, p90=6.0)
        eo = ExpectedOutputs(
            papers_range=papers,
            presentations_range=presentations,
            skill_attainment={"python": 0.8},
        )
        assert eo.skill_attainment["python"] == 0.8

    def test_risk_contribution(self):
        from jarvis_core.decision.schema import RiskContribution

        rc = RiskContribution(name="Tech Risk", contribution=0.3, score=0.7, weight=1.5)
        assert rc.contribution == 0.3

    def test_sensitivity_item(self):
        from jarvis_core.decision.schema import SensitivityItem

        si = SensitivityItem(assumption_id="A1", name="Setup Time", impact_score=0.85)
        assert si.impact_score == 0.85

    def test_decision_result(self):
        from jarvis_core.decision.schema import (
            DecisionResult,
            ExpectedOutputs,
            ProbabilityRange,
            DISCLAIMER_TEXT,
        )

        result = DecisionResult(
            option_id="O1",
            label="Test",
            success_probability=ProbabilityRange(p10=0.3, p50=0.5, p90=0.7),
            expected_outputs=ExpectedOutputs(
                papers_range=ProbabilityRange(p10=1, p50=2, p90=3),
                presentations_range=ProbabilityRange(p10=2, p50=3, p90=5),
                skill_attainment={"ml": 0.9},
            ),
            top_risks=[],
            sensitivity=[],
            mvp_plan={"phase1": "setup"},
            kill_criteria=["6 months no progress"],
        )
        assert result.disclaimer == DISCLAIMER_TEXT

    def test_decision_comparison(self):
        from jarvis_core.decision.schema import DecisionComparison

        dc = DecisionComparison(results=[])
        assert len(dc.results) == 0


# ============================================================
# Tests for risk_factors.py
# ============================================================


class TestRiskFactorDefinition:
    """Tests for RiskFactorDefinition."""

    def test_default_risk_factors_exist(self):
        from jarvis_core.decision.risk_factors import DEFAULT_RISK_FACTORS

        assert len(DEFAULT_RISK_FACTORS) == 7
        names = [f.name for f in DEFAULT_RISK_FACTORS]
        assert "Technical Risk" in names
        assert "Data Risk" in names

    def test_risk_factor_definition_frozen(self):
        from jarvis_core.decision.risk_factors import RiskFactorDefinition

        rfd = RiskFactorDefinition(name="Test", description="Test desc")
        with pytest.raises(Exception):
            rfd.name = "Changed"


class TestDefaultRiskInputs:
    """Tests for default_risk_inputs function."""

    def test_default_risk_inputs_returns_list(self):
        from jarvis_core.decision.risk_factors import default_risk_inputs

        inputs = default_risk_inputs()
        assert len(inputs) == 7
        for inp in inputs:
            assert inp.score.value == 0.5
            assert inp.weight.value == 1.0


# ============================================================
# Tests for simulator.py
# ============================================================


class TestSampleDistribution:
    """Tests for sample_distribution function."""

    def test_sample_triangular(self):
        from jarvis_core.decision.simulator import sample_distribution
        from jarvis_core.decision.schema import TriangularDistribution, RationaleValue

        dist = TriangularDistribution(
            type="triangular",
            low=RationaleValue(value=1.0, rationale="min"),
            mode=RationaleValue(value=5.0, rationale="mode"),
            high=RationaleValue(value=10.0, rationale="max"),
        )
        random.seed(42)
        sample = sample_distribution(dist)
        assert 1.0 <= sample <= 10.0

    def test_sample_normal(self):
        from jarvis_core.decision.simulator import sample_distribution
        from jarvis_core.decision.schema import NormalDistribution, RationaleValue

        dist = NormalDistribution(
            type="normal",
            mean=RationaleValue(value=5.0, rationale="mean"),
            std=RationaleValue(value=1.0, rationale="std"),
        )
        random.seed(42)
        sample = sample_distribution(dist)
        assert sample >= 0.0  # max(0, ...) is applied

    def test_sample_lognormal(self):
        from jarvis_core.decision.simulator import sample_distribution
        from jarvis_core.decision.schema import LogNormalDistribution, RationaleValue

        dist = LogNormalDistribution(
            type="lognormal",
            mean=RationaleValue(value=1.0, rationale="mean"),
            sigma=RationaleValue(value=0.5, rationale="sigma"),
        )
        random.seed(42)
        sample = sample_distribution(dist)
        assert sample > 0.0

    def test_sample_unsupported_type(self):
        from jarvis_core.decision.simulator import sample_distribution

        class FakeDistribution:
            type = "unknown"

        with pytest.raises(ValueError, match="Unsupported distribution type"):
            sample_distribution(FakeDistribution())


class TestPercentile:
    """Tests for _percentile function."""

    def test_percentile_empty_list(self):
        from jarvis_core.decision.simulator import _percentile

        assert _percentile([], 50) == 0.0

    def test_percentile_single_value(self):
        from jarvis_core.decision.simulator import _percentile

        assert _percentile([5.0], 50) == 5.0

    def test_percentile_multiple_values(self):
        from jarvis_core.decision.simulator import _percentile

        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert _percentile(values, 50) == 3.0
        assert _percentile(values, 0) == 1.0
        assert _percentile(values, 100) == 5.0


class TestCorrelation:
    """Tests for _correlation function."""

    def test_correlation_empty(self):
        from jarvis_core.decision.simulator import _correlation

        assert _correlation([], []) == 0.0

    def test_correlation_no_variance(self):
        from jarvis_core.decision.simulator import _correlation

        assert _correlation([5.0, 5.0, 5.0], [1, 1, 1]) == 0.0

    def test_correlation_positive(self):
        from jarvis_core.decision.simulator import _correlation

        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [1, 2, 3, 4, 5]
        corr = _correlation(xs, ys)
        assert corr > 0.99  # Perfect positive correlation


class TestAssignTask:
    """Tests for _assign_task helper."""

    def test_assign_task_setup(self):
        from jarvis_core.decision.simulator import _assign_task
        from jarvis_core.decision.schema import Assumption, TriangularDistribution, RationaleValue

        dist = TriangularDistribution(
            type="triangular",
            low=RationaleValue(value=1.0, rationale="min"),
            mode=RationaleValue(value=2.0, rationale="mode"),
            high=RationaleValue(value=3.0, rationale="max"),
        )
        assumption = Assumption(
            assumption_id="A1",
            name="環境構築期間",
            distribution=dist,
            rationale="test",
        )
        assert _assign_task(assumption) == "setup"

    def test_assign_task_general(self):
        from jarvis_core.decision.simulator import _assign_task
        from jarvis_core.decision.schema import Assumption, TriangularDistribution, RationaleValue

        dist = TriangularDistribution(
            type="triangular",
            low=RationaleValue(value=1.0, rationale="min"),
            mode=RationaleValue(value=2.0, rationale="mode"),
            high=RationaleValue(value=3.0, rationale="max"),
        )
        assumption = Assumption(
            assumption_id="A1",
            name="その他の期間",
            distribution=dist,
            rationale="test",
        )
        assert _assign_task(assumption) == "general"


class TestSimulateOption:
    """Tests for simulate_option function."""

    def test_simulate_option_basic(self):
        from jarvis_core.decision.simulator import simulate_option
        from jarvis_core.decision.schema import (
            Option,
            Assumption,
            Constraints,
            Dependencies,
            TriangularDistribution,
            RationaleValue,
        )

        option = Option(
            option_id="O1",
            label="Test Option",
            goal="Test goal",
            theme="Test theme",
            time_horizon_months=RationaleValue(value=24.0, rationale="2 years"),
            constraints=Constraints(
                weekly_hours=RationaleValue(value=40.0, rationale="full-time"),
                budget_level="medium",
                equipment_access="high",
                mentor_support="high",
            ),
            dependencies=Dependencies(must_learn=["python", "ml"], must_access=[]),
        )

        dist = TriangularDistribution(
            type="triangular",
            low=RationaleValue(value=2.0, rationale="min"),
            mode=RationaleValue(value=4.0, rationale="mode"),
            high=RationaleValue(value=8.0, rationale="max"),
        )
        assumptions = [
            Assumption(
                assumption_id="A1",
                name="Setup期間",
                distribution=dist,
                rationale="test",
            )
        ]

        random.seed(42)
        result = simulate_option(option, assumptions, iterations=100)

        assert "success_rate" in result
        assert "success_range" in result
        assert "papers_range" in result
        assert "presentations_range" in result
        assert "contributions" in result
        assert "sensitivity" in result
        assert "skill_attainment" in result
        assert 0 <= result["success_rate"] <= 1


# ============================================================
# Tests for elicitation.py
# ============================================================


class TestTemplatePayload:
    """Tests for template_payload function."""

    def test_template_payload_structure(self):
        from jarvis_core.decision.elicitation import template_payload

        payload = template_payload()

        assert "options" in payload
        assert "assumptions" in payload
        assert "risk_factors" in payload
        assert "disclaimer" in payload
        assert len(payload["options"]) >= 1


class TestValidatePayload:
    """Tests for validate_payload function."""

    def test_validate_payload_valid(self):
        from jarvis_core.decision.elicitation import template_payload, validate_payload

        # Remove non-schema fields from template
        payload = template_payload()
        del payload["risk_factors"]
        del payload["disclaimer"]

        result = validate_payload(payload)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["parsed"] is not None

    def test_validate_payload_invalid(self):
        from jarvis_core.decision.elicitation import validate_payload

        payload = {"options": "invalid", "assumptions": []}
        result = validate_payload(payload)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert result["parsed"] is None


class TestNormalizeRisks:
    """Tests for normalize_risks function."""

    def test_normalize_risks_with_existing(self):
        from jarvis_core.decision.elicitation import normalize_risks
        from jarvis_core.decision.schema import (
            Option,
            Constraints,
            Dependencies,
            RationaleValue,
            RiskFactorInput,
        )

        option = Option(
            option_id="O1",
            label="Test",
            goal="Test goal",
            theme="Test theme",
            time_horizon_months=RationaleValue(value=12.0, rationale="1 year"),
            constraints=Constraints(
                weekly_hours=RationaleValue(value=40.0, rationale="full-time"),
                budget_level="low",
                equipment_access="low",
                mentor_support="low",
            ),
            dependencies=Dependencies(),
            risk_factors=[
                RiskFactorInput(
                    name="Custom Risk",
                    score=RationaleValue(value=0.8, rationale="high"),
                    weight=RationaleValue(value=2.0, rationale="important"),
                )
            ],
        )

        normalized = normalize_risks([option])
        assert len(normalized) == 1
        assert len(normalized[0].risk_factors) == 1
        assert normalized[0].risk_factors[0].name == "Custom Risk"

    def test_normalize_risks_without_existing(self):
        from jarvis_core.decision.elicitation import normalize_risks
        from jarvis_core.decision.schema import Option, Constraints, Dependencies, RationaleValue

        option = Option(
            option_id="O1",
            label="Test",
            goal="Test goal",
            theme="Test theme",
            time_horizon_months=RationaleValue(value=12.0, rationale="1 year"),
            constraints=Constraints(
                weekly_hours=RationaleValue(value=40.0, rationale="full-time"),
                budget_level="low",
                equipment_access="low",
                mentor_support="low",
            ),
            dependencies=Dependencies(),
        )

        normalized = normalize_risks([option])
        assert len(normalized) == 1
        assert len(normalized[0].risk_factors) == 7  # Default risk factors


# ============================================================
# Tests for planner.py
# ============================================================


class TestAssessPlanTime:
    """Tests for assess_plan_time function."""

    def test_assess_plan_time_no_delay(self):
        from jarvis_core.decision.planner import assess_plan_time
        from jarvis_core.time.schema import TimeSchema, VariableBlock

        plan = {"research_hours_week": 20.0, "additional_hours_week": 5.0}
        time_schema = TimeSchema(
            week_hours=168.0,
            fixed={},
            variable={"research": VariableBlock(min=10.0, target=30.0, max=50.0)},
        )

        result = assess_plan_time(plan, time_schema)

        assert result.required_research_hours == 25.0
        assert result.available_research_hours == 30.0
        assert result.delay_risk is False
        assert result.delay_months == 0
        assert result.delay_cost == 0.0

    def test_assess_plan_time_with_delay(self):
        from jarvis_core.decision.planner import assess_plan_time
        from jarvis_core.time.schema import TimeSchema, VariableBlock

        plan = {
            "research_hours_week": 50.0,
            "additional_hours_week": 10.0,
            "delay_months": 3,
            "housing_cost_monthly": 80000,
        }
        time_schema = TimeSchema(
            week_hours=168.0,
            fixed={},
            variable={"research": VariableBlock(min=10.0, target=40.0, max=60.0)},
        )

        result = assess_plan_time(plan, time_schema)

        assert result.required_research_hours == 60.0
        assert result.available_research_hours == 40.0
        assert result.delay_risk is True
        assert result.delay_months == 3
        assert result.delay_cost == 240000.0
        assert len(result.notes) >= 2


# ============================================================
# Tests for model.py
# ============================================================


class TestEvaluateOptions:
    """Tests for evaluate_options function."""

    @patch("jarvis_core.decision.model.simulate_option")
    @patch("jarvis_core.decision.model.build_mvp_plan")
    @patch("jarvis_core.decision.model.build_kill_criteria")
    def test_evaluate_options(self, mock_kill, mock_mvp, mock_simulate):
        from jarvis_core.decision.model import evaluate_options
        from jarvis_core.decision.schema import (
            Option,
            Assumption,
            Constraints,
            Dependencies,
            TriangularDistribution,
            RationaleValue,
        )

        mock_simulate.return_value = {
            "success_range": {"p10": 0.3, "p50": 0.5, "p90": 0.7},
            "papers_range": {"p10": 1, "p50": 2, "p90": 3},
            "presentations_range": {"p10": 2, "p50": 3, "p90": 5},
            "skill_attainment": {"python": 0.8},
            "contributions": [],
            "sensitivity": [],
        }
        mock_mvp.return_value = {"phase1": "setup"}
        mock_kill.return_value = ["No progress in 6 months"]

        option = Option(
            option_id="O1",
            label="Test Option",
            goal="Test goal",
            theme="Test theme",
            time_horizon_months=RationaleValue(value=24.0, rationale="2 years"),
            constraints=Constraints(
                weekly_hours=RationaleValue(value=40.0, rationale="full-time"),
                budget_level="medium",
                equipment_access="high",
                mentor_support="high",
            ),
            dependencies=Dependencies(),
        )

        dist = TriangularDistribution(
            type="triangular",
            low=RationaleValue(value=1.0, rationale="min"),
            mode=RationaleValue(value=2.0, rationale="mode"),
            high=RationaleValue(value=4.0, rationale="max"),
        )
        assumptions = [
            Assumption(
                assumption_id="A1",
                name="Test Assumption",
                distribution=dist,
                rationale="test",
            )
        ]

        result = evaluate_options([option], assumptions)

        assert len(result.results) == 1
        assert result.results[0].option_id == "O1"
        assert result.results[0].success_probability.p50 == 0.5
