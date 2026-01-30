"""Report Schema Definitions (Phase 2-ΩΩ).

Defines the structure of conclusions in reports to eliminate ambiguity
and enforce evidence-driven output.
"""

from dataclasses import dataclass
from typing import Literal

# Type definitions
SupportLevel = Literal["Strong", "Medium", "Weak", "None"]
UncertaintyLabel = Literal["確定", "高信頼", "要注意", "推測"]
ClaimType = Literal["Background", "Mechanism", "Efficacy", "Safety", "Biomarker"]


@dataclass
class Conclusion:
    """A single conclusion in the report.

    Each conclusion must be backed by evidence and have explicit uncertainty.
    """

    conclusion_text: str
    claim_id: str
    evidence_ids: list[str]
    support_level: SupportLevel
    uncertainty_label: UncertaintyLabel
    notes: str = ""

    def to_markdown(self) -> str:
        """Convert to markdown format for report."""
        lines = [
            f"- 結論: {self.conclusion_text}",
            f"  Claim: {self.claim_id}",
            f"  Evidence: [{', '.join(self.evidence_ids) if self.evidence_ids else '根拠不足'}]",
            f"  Support: {self.support_level}",
            f"  Uncertainty: {self.uncertainty_label}",
        ]

        if self.notes:
            lines.append(f"  Notes: {self.notes}")
        else:
            lines.append("  Notes: —")

        return "\n".join(lines)


@dataclass
class ReportMetadata:
    """Metadata for the entire report."""

    total_papers: int
    total_claims: int
    supported_claims: int
    support_rate: float
    quality_warnings: list[str]


def validate_conclusion(conclusion: Conclusion) -> list[str]:
    """Validate a conclusion for quality issues.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Rule 1: Strong/Medium must have evidence
    if conclusion.support_level in ["Strong", "Medium"] and not conclusion.evidence_ids:
        errors.append(
            f"Claim {conclusion.claim_id}: {conclusion.support_level} support without evidence IDs"
        )

    # Rule 2: None support must not have assertive text
    if conclusion.support_level == "None":
        assertive_terms = ["である", "確実", "証明", "明らか"]
        if any(term in conclusion.conclusion_text for term in assertive_terms):
            errors.append(f"Claim {conclusion.claim_id}: Assertive language with None support")

    # Rule 3: Uncertainty must match support level
    expected_uncertainty = {"Strong": "確定", "Medium": "高信頼", "Weak": "要注意", "None": "推測"}

    if conclusion.uncertainty_label != expected_uncertainty[conclusion.support_level]:
        errors.append(
            f"Claim {conclusion.claim_id}: Uncertainty mismatch "
            f"(expected {expected_uncertainty[conclusion.support_level]}, "
            f"got {conclusion.uncertainty_label})"
        )

    return errors