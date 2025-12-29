"""Time allocation schema for weekly planning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

DEFAULT_NOTE = "（推測です）"


@dataclass
class FixedHours:
    sleep: int
    meals: int
    commute: int

    def total(self) -> int:
        return self.sleep + self.meals + self.commute


@dataclass
class VariableRange:
    min: int
    target: int
    max: int
    note: str = DEFAULT_NOTE


@dataclass
class VariableHours:
    research: VariableRange
    coursework: VariableRange
    ra_ta: VariableRange
    part_time: VariableRange
    rest: VariableRange

    def as_dict(self) -> Dict[str, VariableRange]:
        return {
            "research": self.research,
            "coursework": self.coursework,
            "ra_ta": self.ra_ta,
            "part_time": self.part_time,
            "rest": self.rest,
        }


@dataclass
class WeekAllocation:
    week_hours: int
    fixed: FixedHours
    variable: VariableHours

    def fixed_total(self) -> int:
        return self.fixed.total()

    def variable_target_total(self) -> int:
        return sum(item.target for item in self.variable.as_dict().values())

    def variable_max_total(self) -> int:
        return sum(item.max for item in self.variable.as_dict().values())

    def available_hours(self) -> int:
        return self.week_hours - self.fixed_total()

    def work_hours_target(self) -> int:
        return (
            self.variable.research.target
            + self.variable.ra_ta.target
            + self.variable.part_time.target
        )

    def work_hours_max(self) -> int:
        return (
            self.variable.research.max
            + self.variable.ra_ta.max
            + self.variable.part_time.max
        )

    def overwork_flag(self) -> bool:
        """Flag overwork when research/ra/part-time exceed available hours."""
        return self.work_hours_target() > self.available_hours()

    def sleep_hours_per_day(self) -> float:
        return self.fixed.sleep / 7


def default_week_allocation() -> WeekAllocation:
    return WeekAllocation(
        week_hours=168,
        fixed=FixedHours(sleep=56, meals=14, commute=10),
        variable=VariableHours(
            research=VariableRange(min=30, target=45, max=60),
            coursework=VariableRange(min=0, target=5, max=10),
            ra_ta=VariableRange(min=0, target=10, max=20),
            part_time=VariableRange(min=0, target=0, max=10),
            rest=VariableRange(min=10, target=15, max=20),
        ),
    )
