"""Time allocation schema for P10."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VariableBlock:
    min: float
    target: float
    max: float


@dataclass
class TimeSchema:
    week_hours: float
    fixed: dict[str, float]
    variable: dict[str, VariableBlock]

    def fixed_total(self) -> float:
        return sum(self.fixed.values())

    def variable_targets_total(self) -> float:
        return sum(block.target for block in self.variable.values())

    def available_variable_hours(self) -> float:
        return max(self.week_hours - self.fixed_total(), 0.0)

    def working_hours(self) -> float:
        return sum(
            self.variable[name].target
            for name in ["research", "ra_ta", "part_time"]
            if name in self.variable
        )

    def working_hours_max(self) -> float:
        return sum(
            self.variable[name].max
            for name in ["research", "ra_ta", "part_time"]
            if name in self.variable
        )


DEFAULT_TIME_SCHEMA = TimeSchema(
    week_hours=168,
    fixed={
        "sleep": 56,
        "meals": 14,
        "commute": 10,
    },
    variable={
        "research": VariableBlock(min=30, target=45, max=60),
        "coursework": VariableBlock(min=0, target=5, max=10),
        "ra_ta": VariableBlock(min=0, target=10, max=20),
        "part_time": VariableBlock(min=0, target=0, max=10),
        "rest": VariableBlock(min=10, target=15, max=20),
    },
)
