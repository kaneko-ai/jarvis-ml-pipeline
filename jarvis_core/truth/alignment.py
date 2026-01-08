"""Claim↔Fact Alignment v2.

Per V4-T02, this provides strict alignment checking with:
- Token overlap
- Locator consistency (page, paragraph)
- Machine-readable mismatch reasons
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.schema import Fact


@dataclass
class AlignmentResult:
    """Result of alignment check."""

    claim: str
    status: str  # aligned, partial, misaligned
    score: float  # 0-1
    token_overlap: float
    locator_match: bool
    mismatch_reasons: list[str]
    matched_fact: str | None = None

    def to_dict(self) -> dict:
        return {
            "claim": self.claim[:100],
            "status": self.status,
            "score": self.score,
            "token_overlap": self.token_overlap,
            "locator_match": self.locator_match,
            "mismatch_reasons": self.mismatch_reasons,
            "matched_fact": self.matched_fact,
        }


def tokenize(text: str) -> set:
    """Tokenize text for overlap calculation."""
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and"}
    words = text.lower().split()
    return {w for w in words if w not in stopwords and len(w) > 2}


def calculate_token_overlap(text1: str, text2: str) -> float:
    """Calculate token overlap ratio."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1:
        return 0.0

    overlap = len(tokens1 & tokens2)
    return overlap / len(tokens1)


def check_locator_match(claim_locator: str, fact_locators: list[str]) -> bool:
    """Check if locators are consistent."""
    if not claim_locator or not fact_locators:
        return False

    claim_lower = claim_locator.lower()
    for loc in fact_locators:
        if claim_lower in loc.lower() or loc.lower() in claim_lower:
            return True

    return False


def check_alignment_v2(
    claim: str,
    facts: list[Fact],
    claim_locator: str = "",
    min_overlap: float = 0.3,
) -> AlignmentResult:
    """Check claim-fact alignment with strict criteria.

    Args:
        claim: The claim text.
        facts: List of supporting facts.
        claim_locator: Optional locator for the claim.
        min_overlap: Minimum token overlap threshold.

    Returns:
        AlignmentResult with detailed analysis.
    """
    if not facts:
        return AlignmentResult(
            claim=claim,
            status="misaligned",
            score=0.0,
            token_overlap=0.0,
            locator_match=False,
            mismatch_reasons=["No supporting facts provided"],
        )

    best_overlap = 0.0
    best_fact = None
    all_locators = []
    mismatch_reasons = []

    for fact in facts:
        # Check token overlap with fact statement
        overlap = calculate_token_overlap(claim, fact.statement)

        # Also check evidence snippets
        for ref in fact.evidence_refs:
            if ref.text_snippet:
                snippet_overlap = calculate_token_overlap(claim, ref.text_snippet)
                overlap = max(overlap, snippet_overlap)
            all_locators.append(ref.source_locator)

        if overlap > best_overlap:
            best_overlap = overlap
            best_fact = fact.statement

    # Check locator
    locator_match = check_locator_match(claim_locator, all_locators) if claim_locator else True

    # Determine status and reasons
    if best_overlap < min_overlap:
        mismatch_reasons.append(f"Token overlap too low: {best_overlap:.2f} < {min_overlap}")

    if claim_locator and not locator_match:
        mismatch_reasons.append(f"Locator mismatch: {claim_locator} not in facts")

    # Calculate final score
    score = best_overlap * (1.0 if locator_match else 0.8)

    if score >= 0.6:
        status = "aligned"
    elif score >= 0.3:
        status = "partial"
    else:
        status = "misaligned"

    return AlignmentResult(
        claim=claim,
        status=status,
        score=round(score, 3),
        token_overlap=round(best_overlap, 3),
        locator_match=locator_match,
        mismatch_reasons=mismatch_reasons,
        matched_fact=best_fact[:100] if best_fact else None,
    )
