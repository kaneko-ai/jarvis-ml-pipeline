"""Decision Intelligence schema definitions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, validator

DISCLAIMER_TEXT = "仮定に依存する（推測です）"


class RationaleValue(BaseModel):
    """Numeric value that requires a rationale."""

    value: float
    rationale: str = Field(..., min_length=1)

    @validator("rationale")
    def _rationale_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("rationale is required for numeric values")
        return value


class TriangularDistribution(BaseModel):
    """Triangular distribution parameters."""

    type: Literal["triangular"]
    low: RationaleValue
    mode: RationaleValue
    high: RationaleValue
    unit: str = "months"


class NormalDistribution(BaseModel):
    """Normal distribution parameters."""

    type: Literal["normal"]
    mean: RationaleValue
    std: RationaleValue
    unit: str = "months"


class LogNormalDistribution(BaseModel):
    """Log-normal distribution parameters."""

    type: Literal["lognormal"]
    mean: RationaleValue
    sigma: RationaleValue
    unit: str = "months"


Distribution = TriangularDistribution | NormalDistribution | LogNormalDistribution


class Assumption(BaseModel):
    """Assumption with distribution and rationale."""

    assumption_id: str
    name: str
    distribution: Distribution
    rationale: str = Field(..., min_length=1)
    applies_to: str | None = None


class Constraints(BaseModel):
    """Constraints for an option."""

    weekly_hours: RationaleValue
    budget_level: str
    equipment_access: str
    mentor_support: str


class Dependencies(BaseModel):
    """Dependencies for an option."""

    must_learn: list[str] = []
    must_access: list[str] = []


class RiskFactorInput(BaseModel):
    """Risk factor input with score and weight."""

    name: str
    score: RationaleValue
    weight: RationaleValue
    rationale: str | None = None


class Option(BaseModel):
    """Decision option to evaluate."""

    option_id: str
    label: str
    goal: str
    theme: str
    time_horizon_months: RationaleValue
    constraints: Constraints
    dependencies: Dependencies
    risk_factors: list[RiskFactorInput] | None = None


class UserConstraints(BaseModel):
    """User-level constraints for decision simulation."""

    max_weekly_hours: RationaleValue | None = None
    preferred_budget_level: str | None = None
    notes: str | None = None


class DecisionInput(BaseModel):
    """Input payload for decision simulation."""

    options: list[Option]
    assumptions: list[Assumption]
    user_constraints: UserConstraints | None = None


class ProbabilityRange(BaseModel):
    """Probability range output."""

    p10: float
    p50: float
    p90: float


class ExpectedOutputs(BaseModel):
    """Expected outputs for each option."""

    papers_range: ProbabilityRange
    presentations_range: ProbabilityRange
    skill_attainment: dict


class RiskContribution(BaseModel):
    """Risk contribution output."""

    name: str
    contribution: float
    score: float
    weight: float


class SensitivityItem(BaseModel):
    """Sensitivity analysis item."""

    assumption_id: str
    name: str
    impact_score: float


class DecisionResult(BaseModel):
    """Decision result for a single option."""

    option_id: str
    label: str
    success_probability: ProbabilityRange
    expected_outputs: ExpectedOutputs
    top_risks: list[RiskContribution]
    sensitivity: list[SensitivityItem]
    mvp_plan: dict
    kill_criteria: list[str]
    disclaimer: str = DISCLAIMER_TEXT


class DecisionComparison(BaseModel):
    """Comparison response."""

    results: list[DecisionResult]
    disclaimer: str = DISCLAIMER_TEXT