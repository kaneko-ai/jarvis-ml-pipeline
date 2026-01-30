"""Decision probability estimation model."""

from __future__ import annotations

from .planner import build_kill_criteria, build_mvp_plan
from .schema import (
    Assumption,
    DecisionComparison,
    DecisionResult,
    ExpectedOutputs,
    Option,
    ProbabilityRange,
    RiskContribution,
    SensitivityItem,
)
from .simulator import simulate_option


def evaluate_options(options: list[Option], assumptions: list[Assumption]) -> DecisionComparison:
    """Evaluate options and return comparison results."""
    results: list[DecisionResult] = []

    for option in options:
        simulation = simulate_option(option, assumptions)
        success_range = ProbabilityRange(**simulation["success_range"])
        papers_range = ProbabilityRange(**simulation["papers_range"])
        presentations_range = ProbabilityRange(**simulation["presentations_range"])

        expected_outputs = ExpectedOutputs(
            papers_range=papers_range,
            presentations_range=presentations_range,
            skill_attainment=simulation["skill_attainment"],
        )

        top_risks = [RiskContribution(**risk) for risk in simulation["contributions"]]
        sensitivity = [SensitivityItem(**item) for item in simulation["sensitivity"]]

        result = DecisionResult(
            option_id=option.option_id,
            label=option.label,
            success_probability=success_range,
            expected_outputs=expected_outputs,
            top_risks=top_risks,
            sensitivity=sensitivity,
            mvp_plan=build_mvp_plan(option),
            kill_criteria=build_kill_criteria(option),
        )
        results.append(result)

    return DecisionComparison(results=results)
