"""Claim-Fact Alignment Checker.

Per V4-B2, this detects misalignment between claims and facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.schema import ArtifactBase, Fact


@dataclass
class AlignmentResult:
    """Result of claim-fact alignment check."""

    claim_text: str
    status: str  # "aligned", "partial", "misaligned"
    evidence_coverage: float  # 0-1
    matched_facts: list[str]
    issues: list[str]

    def to_dict(self) -> dict:
        return {
            "claim_text": self.claim_text[:100],
            "status": self.status,
            "evidence_coverage": self.evidence_coverage,
            "matched_facts": self.matched_facts,
            "issues": self.issues,
        }


class ClaimFactChecker:
    """Checks alignment between claims and supporting facts."""

    @staticmethod
    def tokenize(text: str) -> set[str]:
        """Simple tokenization."""
        words = text.lower().split()
        # Remove common words
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        return {w for w in words if w not in stopwords and len(w) > 2}

    @staticmethod
    def calculate_overlap(claim: str, evidence_text: str) -> float:
        """Calculate token overlap between claim and evidence."""
        claim_tokens = ClaimFactChecker.tokenize(claim)
        evidence_tokens = ClaimFactChecker.tokenize(evidence_text)

        if not claim_tokens:
            return 0.0

        overlap = len(claim_tokens & evidence_tokens)
        return overlap / len(claim_tokens)

    def check_alignment(
        self,
        claim: str,
        facts: list[Fact],
        min_coverage: float = 0.3,
    ) -> AlignmentResult:
        """Check if claim aligns with supporting facts.

        Args:
            claim: The claim text.
            facts: List of supporting facts.
            min_coverage: Minimum overlap for alignment.

        Returns:
            AlignmentResult with status and details.
        """
        if not facts:
            return AlignmentResult(
                claim_text=claim,
                status="misaligned",
                evidence_coverage=0.0,
                matched_facts=[],
                issues=["No supporting facts provided"],
            )

        matched_facts = []
        total_overlap = 0.0
        issues = []

        for fact in facts:
            # Check overlap with fact statement
            overlap = self.calculate_overlap(claim, fact.statement)

            # Also check overlap with evidence snippets
            for ref in fact.evidence_refs:
                if ref.text_snippet:
                    overlap = max(overlap, self.calculate_overlap(claim, ref.text_snippet))

            if overlap > min_coverage:
                matched_facts.append(fact.statement[:50])
                total_overlap = max(total_overlap, overlap)

        # Determine status
        if not matched_facts:
            status = "misaligned"
            issues.append("Claim has no supporting facts with sufficient overlap")
        elif total_overlap < 0.5:
            status = "partial"
            issues.append("Claim partially supported by evidence")
        else:
            status = "aligned"

        return AlignmentResult(
            claim_text=claim,
            status=status,
            evidence_coverage=round(total_overlap, 3),
            matched_facts=matched_facts,
            issues=issues,
        )

    def check_artifact(
        self,
        artifact: ArtifactBase,
    ) -> list[AlignmentResult]:
        """Check all inferences in an artifact against facts.

        Args:
            artifact: The artifact to check.

        Returns:
            List of alignment results for each inference.
        """
        results = []

        for inference in artifact.inferences:
            result = self.check_alignment(
                claim=inference.statement,
                facts=artifact.facts,
            )
            results.append(result)

        return results


def check_claim_fact_alignment(
    claims: list[str],
    facts: list[Fact],
) -> list[AlignmentResult]:
    """Convenience function to check multiple claims.

    Args:
        claims: List of claim texts.
        facts: List of supporting facts.

    Returns:
        List of alignment results.
    """
    checker = ClaimFactChecker()
    return [checker.check_alignment(claim, facts) for claim in claims]


def enforce_evidence_ref(statement: str, has_evidence: bool) -> tuple[str, str]:
    """Enforce that facts must have evidence.

    Args:
        statement: The statement.
        has_evidence: Whether evidence is present.

    Returns:
        Tuple of (truth_level, statement).
        Downgrades to INFERENCE if no evidence.
    """
    if has_evidence:
        return ("fact", statement)
    else:
        return ("inference", f"[推定] {statement}")