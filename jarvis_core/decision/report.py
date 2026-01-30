"""Decision report generation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .schema import DISCLAIMER_TEXT, DecisionComparison


def build_markdown_report(comparison: DecisionComparison) -> str:
    """Build a markdown report from decision comparison."""
    lines = [
        "# Decision Intelligence Report",
        f"- Generated: {datetime.utcnow().isoformat()}Z",
        f"- Disclaimer: {DISCLAIMER_TEXT}",
        "",
    ]

    for result in comparison.results:
        lines.extend(
            [
                f"## Option {result.option_id}: {result.label}",
                f"- Success Probability (P10/P50/P90): {result.success_probability.p10:.2f} / {result.success_probability.p50:.2f} / {result.success_probability.p90:.2f}",
                f"- Papers (P10/P50/P90): {result.expected_outputs.papers_range.p10:.2f} / {result.expected_outputs.papers_range.p50:.2f} / {result.expected_outputs.papers_range.p90:.2f}",
                f"- Presentations (P10/P50/P90): {result.expected_outputs.presentations_range.p10:.2f} / {result.expected_outputs.presentations_range.p50:.2f} / {result.expected_outputs.presentations_range.p90:.2f}",
                "",
                "### Top Risks",
            ]
        )
        for risk in result.top_risks:
            lines.append(
                f"- {risk.name}: contribution={risk.contribution:.2f}, score={risk.score:.2f}"
            )

        lines.append("\n### Sensitivity (Top 5)")
        for item in result.sensitivity:
            lines.append(f"- {item.name}: impact={item.impact_score:.2f}")

        lines.append("\n### MVP Plan (90 days)")
        for phase, items in result.mvp_plan.items():
            if phase == "disclaimer":
                continue
            lines.append(f"- {phase}: {', '.join(items)}")

        lines.append("\n### Kill Criteria")
        for criterion in result.kill_criteria:
            lines.append(f"- {criterion}")
        lines.append("")

    return "\n".join(lines)


def build_html_report(markdown_report: str) -> str:
    """Wrap markdown in a simple HTML template."""
    escaped = markdown_report.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped = escaped.replace("\n", "<br>")
    return (
        "<html><head><meta charset='utf-8'><title>Decision Report</title>"
        "<style>body{font-family:Arial,sans-serif;padding:20px;background:#0f0f23;color:#e8e8e8;}"
        "h1,h2,h3{color:#00d4ff;}br{line-height:1.6;}</style></head>"
        f"<body>{escaped}</body></html>"
    )


def write_report_files(comparison: DecisionComparison, output_dir: Path) -> dict[str, Path]:
    """Write markdown and HTML reports to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown_report(comparison)
    html = build_html_report(markdown)

    md_path = output_dir / "decision_report.md"
    html_path = output_dir / "decision_report.html"

    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")

    return {"markdown": md_path, "html": html_path}