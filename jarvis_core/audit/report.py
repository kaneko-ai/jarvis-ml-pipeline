"""Audit Report Generator.

Per V4-D2, this generates audit reports for artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.schema import ArtifactBase


@dataclass
class AuditReport:
    """Audit report for an artifact."""

    artifact_kind: str
    fact_count: int
    inference_count: int
    recommendation_count: int
    evidence_coverage: float  # Percentage of facts with evidence
    weaknesses: list[str]
    truth_distribution: dict
    validation_issues: list[str]

    def to_dict(self) -> dict:
        return {
            "artifact_kind": self.artifact_kind,
            "fact_count": self.fact_count,
            "inference_count": self.inference_count,
            "recommendation_count": self.recommendation_count,
            "evidence_coverage": self.evidence_coverage,
            "weaknesses": self.weaknesses,
            "truth_distribution": self.truth_distribution,
            "validation_issues": self.validation_issues,
        }

    def to_markdown(self) -> str:
        """Generate markdown audit report."""
        lines = [
            "# Audit Report",
            "",
            f"**Artifact Type**: {self.artifact_kind}",
            "",
            "## Truth Distribution",
            f"- Facts: {self.fact_count}",
            f"- Inferences: {self.inference_count}",
            f"- Recommendations: {self.recommendation_count}",
            "",
            f"**Evidence Coverage**: {self.evidence_coverage:.1%}",
            "",
        ]

        if self.weaknesses:
            lines.append("## Weaknesses")
            for w in self.weaknesses:
                lines.append(f"- {w}")
            lines.append("")

        if self.validation_issues:
            lines.append("## Validation Issues")
            for v in self.validation_issues:
                lines.append(f"- {v}")

        return "\n".join(lines)


def generate_audit_report(artifact: ArtifactBase) -> AuditReport:
    """Generate audit report for an artifact.

    Args:
        artifact: The artifact to audit.

    Returns:
        AuditReport with analysis.
    """
    # Count evidence
    total_evidence = 0
    for fact in artifact.facts:
        total_evidence += len(fact.evidence_refs)

    evidence_coverage = 1.0 if not artifact.facts else (
        total_evidence / len(artifact.facts) if total_evidence else 0.0
    )

    # Identify weaknesses
    weaknesses = []

    if not artifact.facts:
        weaknesses.append("No facts with evidence backing")

    if artifact.inferences and not artifact.facts:
        weaknesses.append("Inferences without supporting facts")

    if evidence_coverage < 0.5:
        weaknesses.append("Low evidence coverage")

    # Check metrics range
    for name, value in artifact.metrics.items():
        if not (0 <= value <= 1):
            weaknesses.append(f"Metric '{name}' out of range: {value}")

    # Validation issues
    validation_issues = artifact.validate()

    # Truth distribution
    total = len(artifact.facts) + len(artifact.inferences) + len(artifact.recommendations)
    truth_distribution = {
        "fact_ratio": len(artifact.facts) / total if total else 0,
        "inference_ratio": len(artifact.inferences) / total if total else 0,
        "recommendation_ratio": len(artifact.recommendations) / total if total else 0,
    }

    return AuditReport(
        artifact_kind=artifact.kind,
        fact_count=len(artifact.facts),
        inference_count=len(artifact.inferences),
        recommendation_count=len(artifact.recommendations),
        evidence_coverage=round(evidence_coverage, 3),
        weaknesses=weaknesses,
        truth_distribution=truth_distribution,
        validation_issues=validation_issues,
    )


def generate_bundle_audit(artifacts: list[ArtifactBase]) -> str:
    """Generate audit report for multiple artifacts."""
    lines = ["# Bundle Audit Report", ""]

    total_facts = 0
    total_inferences = 0
    all_weaknesses = []

    for artifact in artifacts:
        report = generate_audit_report(artifact)
        total_facts += report.fact_count
        total_inferences += report.inference_count
        all_weaknesses.extend(report.weaknesses)

    lines.append(f"**Total Artifacts**: {len(artifacts)}")
    lines.append(f"**Total Facts**: {total_facts}")
    lines.append(f"**Total Inferences**: {total_inferences}")
    lines.append("")

    if all_weaknesses:
        lines.append("## Summary Weaknesses")
        for w in set(all_weaknesses):
            lines.append(f"- {w}")

    return "\n".join(lines)
