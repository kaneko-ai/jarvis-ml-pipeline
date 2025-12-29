"""Report builder for finance/time optimization."""
from __future__ import annotations

from typing import Iterable

from jarvis_core.optimization.solver import OptimizationResult


def build_report(results: Iterable[OptimizationResult], format: str = "md") -> str:
    """Build a report in markdown or HTML."""
    lines = []
    if format == "html":
        lines.append("<h1>資金・時間最適化レポート</h1>")
        lines.append("<p>すべての数値は仮定に基づく推測です。</p>")
        for result in results:
            lines.append(
                "<h2>シナリオ {}</h2>".format(result.scenario)
            )
            lines.append("<ul>")
            lines.append(f"<li>status: {result.status}</li>")
            lines.append(f"<li>expected_balance_end: {result.expected_balance_end}</li>")
            lines.append(f"<li>bankruptcy_risk: {result.bankruptcy_risk}</li>")
            lines.append(f"<li>research_hours_avg: {result.research_hours_avg}</li>")
            lines.append(f"<li>overwork_risk: {result.overwork_risk}</li>")
            lines.append(f"<li>recommendation: {result.recommendation}</li>")
            if "minimum_balance" in result.details:
                lines.append(f"<li>minimum_balance: {result.details['minimum_balance']}</li>")
            if "deficit_probability" in result.details:
                lines.append(f"<li>deficit_probability: {result.details['deficit_probability']}</li>")
            lines.append("</ul>")
        return "\n".join(lines)

    lines.append("# 資金・時間最適化レポート")
    lines.append("すべての数値は仮定に基づく推測です。")
    for result in results:
        lines.append(f"## シナリオ {result.scenario}")
        lines.append(f"- status: {result.status}")
        lines.append(f"- expected_balance_end: {result.expected_balance_end}")
        lines.append(f"- bankruptcy_risk: {result.bankruptcy_risk}")
        lines.append(f"- research_hours_avg: {result.research_hours_avg}")
        lines.append(f"- overwork_risk: {result.overwork_risk}")
        lines.append(f"- recommendation: {result.recommendation}")
        if "minimum_balance" in result.details:
            lines.append(f"- minimum_balance: {result.details['minimum_balance']}")
        if "deficit_probability" in result.details:
            lines.append(f"- deficit_probability: {result.details['deficit_probability']}")
    return "\n".join(lines)
