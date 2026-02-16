"""Generate upgrade proposals from radar findings."""

from __future__ import annotations


def build_proposals(findings: list[dict]) -> list[dict]:
    proposals: list[dict] = []
    for finding in findings[:10]:
        tags = finding.get("tags", ["other"])
        proposals.append(
            {
                "title": f"Adopt idea from {finding.get('source', 'source')}",
                "source_id": finding.get("id"),
                "evidence": finding.get("url") or finding.get("title"),
                "delta": f"Potential improvement in {', '.join(tags)}",
                "risk": "Implementation and compatibility risks must be validated.",
                "effort": "M",
                "impact_scope": "pipeline+docs",
            }
        )
    return proposals


def proposals_markdown(proposals: list[dict]) -> str:
    lines = ["# Upgrade Proposals", ""]
    if not proposals:
        lines.append("- No proposals generated.")
        return "\n".join(lines) + "\n"
    for idx, proposal in enumerate(proposals, start=1):
        lines.extend(
            [
                f"## Proposal {idx}: {proposal['title']}",
                f"- Evidence: {proposal['evidence']}",
                f"- Delta: {proposal['delta']}",
                f"- Risk: {proposal['risk']}",
                f"- Effort: {proposal['effort']}",
                f"- Impact scope: {proposal['impact_scope']}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"
