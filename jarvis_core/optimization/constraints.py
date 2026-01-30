"""Constraint evaluation for resource optimization."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis_core.finance.schema import MonthlyCashflow
from jarvis_core.time.schema import TimeSchema


@dataclass
class ConstraintViolation:
    name: str
    severity: str
    detail: str


@dataclass
class ConstraintReport:
    hard_violations: list[ConstraintViolation] = field(default_factory=list)
    soft_violations: list[ConstraintViolation] = field(default_factory=list)

    def status(self) -> str:
        if self.hard_violations:
            return "infeasible"
        if self.soft_violations:
            return "risky"
        return "feasible"


def evaluate_constraints(
    cashflows: list[MonthlyCashflow],
    time_schema: TimeSchema,
    initial_savings: float,
    research_required: float | None = None,
) -> ConstraintReport:
    report = ConstraintReport()

    for month in cashflows:
        if month.expected_balance_end() < 0:
            report.hard_violations.append(
                ConstraintViolation(
                    name="deficit",
                    severity="hard",
                    detail=f"{month.month} に月末残高が赤字です（推測です）",
                )
            )
            break

    sleep_hours = time_schema.fixed.get("sleep", 0.0)
    if sleep_hours < 42:
        report.hard_violations.append(
            ConstraintViolation(
                name="sleep",
                severity="hard",
                detail="平均睡眠時間が6h/日を下回ります（推測です）",
            )
        )

    working_hours = time_schema.working_hours()
    if working_hours > 80:
        report.hard_violations.append(
            ConstraintViolation(
                name="overwork",
                severity="hard",
                detail="週労働時間が80hを超過しています（推測です）",
            )
        )

    if time_schema.working_hours() > time_schema.working_hours_max():
        report.soft_violations.append(
            ConstraintViolation(
                name="overwork_flag",
                severity="soft",
                detail="研究・RA/TA・バイトの合計が想定上限を超過しています（推測です）",
            )
        )

    research_target = time_schema.variable.get("research")
    if research_target and research_target.target > time_schema.available_variable_hours():
        report.soft_violations.append(
            ConstraintViolation(
                name="research_capacity",
                severity="soft",
                detail="研究時間ターゲットが可処分時間を上回ります（推測です）",
            )
        )

    if research_required is not None and research_target:
        if research_required > research_target.target:
            report.soft_violations.append(
                ConstraintViolation(
                    name="research_delay",
                    severity="soft",
                    detail="研究計画が時間配分のターゲットを超過しています（推測です）",
                )
            )

    rest_block = time_schema.variable.get("rest")
    if rest_block and rest_block.target < rest_block.min:
        report.soft_violations.append(
            ConstraintViolation(
                name="rest",
                severity="soft",
                detail="余暇時間が最低基準を下回ります（推測です）",
            )
        )

    final_balance = cashflows[-1].expected_balance_end() if cashflows else initial_savings
    if final_balance < initial_savings * 0.5:
        report.soft_violations.append(
            ConstraintViolation(
                name="savings_drop",
                severity="soft",
                detail="貯蓄残高が初期値を大きく下回ります（推測です）",
            )
        )

    return report
