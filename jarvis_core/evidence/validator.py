"""Evidence validation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis_core.evidence.store import EvidenceStore
from jarvis_core.evidence.uncertainty import determine_uncertainty_label


@dataclass
class EvidenceValidation:
    """Result of validating a conclusion against evidence."""

    is_valid: bool
    violations: list[str] = field(default_factory=list)
    uncertainty_label: str = "unknown"


class EvidenceValidator:
    """Validate conclusions against evidence requirements."""

    def validate_conclusion(
        self,
        conclusion: str,
        evidence_ids: list[str],
        evidence_store: EvidenceStore,
    ) -> EvidenceValidation:
        """Validate that a conclusion references evidence IDs.

        Args:
            conclusion: Conclusion text (unused in validation for now).
            evidence_ids: Evidence IDs cited for the conclusion.
            evidence_store: Evidence store for validating IDs.

        Returns:
            EvidenceValidation result.
        """
        violations: list[str] = []

        if not evidence_ids:
            violations.append("MISSING_EVIDENCE_ID")

        missing_ids = [eid for eid in evidence_ids if not evidence_store.has_chunk(eid)]
        if missing_ids:
            violations.append("INVALID_EVIDENCE_ID")

        is_valid = len(violations) == 0
        valid_count = len(evidence_ids) - len(missing_ids)
        strength = valid_count / max(len(evidence_ids), 1)
        uncertainty_label = determine_uncertainty_label(strength)
        return EvidenceValidation(
            is_valid=is_valid, violations=violations, uncertainty_label=uncertainty_label
        )
