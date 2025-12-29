"""Decision probability estimation model."""
from __future__ import annotations

from typing import Dict, List

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
from .planner import build_mvp_plan, build_kill_criteria


def evaluate_options(options: List[Option], assumptions: List[Assumption]) -> DecisionComparison:
    """Evaluate options and return comparison results."""
    results: List[DecisionResult] = []

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
