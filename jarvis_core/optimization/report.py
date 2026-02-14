"""Report generator for finance optimization."""

from __future__ import annotations

from datetime import datetime, timezone

from jarvis_core.finance.scenarios import ScenarioResult
from jarvis_core.optimization.solver import ScenarioEvaluation

ASSUMPTION_NOTE = "（推測です）"


def _scenario_line(evaluation: ScenarioEvaluation) -> str:
    return (
        f"- {evaluation.scenario}: status={evaluation.status}, "
        f"expected_balance_end={evaluation.expected_balance_end:.0f}, "
        f"bankruptcy_risk={evaluation.bankruptcy_risk:.2f}, "
        f"research_hours_avg={evaluation.research_hours_avg:.1f} {ASSUMPTION_NOTE}"
    )


def generate_markdown(
    scenarios: dict[str, ScenarioResult],
    evaluations: dict[str, ScenarioEvaluation],
) -> str:
    lines = [
        "# P10 Resource Optimization Report",
        f"> Generated at {datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z",
        "",
        f"> すべての結果は仮定依存です {ASSUMPTION_NOTE}",
        "",
        "## Scenario Summary",
    ]
    for scenario_id, result in scenarios.items():
        eval_result = evaluations[scenario_id]
        lines.append(f"### {scenario_id} - {result.name}")
        lines.append(_scenario_line(eval_result))
        lines.append(f"- minimum_balance={eval_result.minimum_balance:.0f} {ASSUMPTION_NOTE}")
        lines.append(f"- recommendation: {eval_result.recommendation}")
        if eval_result.constraint_report.hard_violations:
            lines.append("- hard violations:")
            for violation in eval_result.constraint_report.hard_violations:
                lines.append(f"  - {violation.detail}")
        if eval_result.constraint_report.soft_violations:
            lines.append("- soft violations:")
            for violation in eval_result.constraint_report.soft_violations:
                lines.append(f"  - {violation.detail}")
        lines.append("")
    return "\n".join(lines)


def generate_html(
    scenarios: dict[str, ScenarioResult],
    evaluations: dict[str, ScenarioEvaluation],
) -> str:
    sections = [
        "<h1>P10 Resource Optimization Report</h1>",
        f"<p>Generated at {datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z</p>",
        f"<p>すべての結果は仮定依存です {ASSUMPTION_NOTE}</p>",
    ]
    for scenario_id, result in scenarios.items():
        evaluation = evaluations[scenario_id]
        sections.append(f"<h2>{scenario_id} - {result.name}</h2>")
        sections.append(
            "<ul>"
            f"<li>status: {evaluation.status}</li>"
            f"<li>expected_balance_end: {evaluation.expected_balance_end:.0f} {ASSUMPTION_NOTE}</li>"
            f"<li>bankruptcy_risk: {evaluation.bankruptcy_risk:.2f} {ASSUMPTION_NOTE}</li>"
            f"<li>research_hours_avg: {evaluation.research_hours_avg:.1f} {ASSUMPTION_NOTE}</li>"
            f"<li>minimum_balance: {evaluation.minimum_balance:.0f} {ASSUMPTION_NOTE}</li>"
            f"<li>recommendation: {evaluation.recommendation}</li>"
            "</ul>"
        )
        if evaluation.constraint_report.hard_violations:
            sections.append("<strong>Hard violations</strong><ul>")
            for violation in evaluation.constraint_report.hard_violations:
                sections.append(f"<li>{violation.detail}</li>")
            sections.append("</ul>")
        if evaluation.constraint_report.soft_violations:
            sections.append("<strong>Soft violations</strong><ul>")
            for violation in evaluation.constraint_report.soft_violations:
                sections.append(f"<li>{violation.detail}</li>")
            sections.append("</ul>")
    return "\n".join(sections)
