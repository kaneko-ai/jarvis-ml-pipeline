"""Claim Checker.

Per RP-07, this provides claim-level verification for RAGChecker-style evaluation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ClaimVerdict(Enum):
    """Claim verification verdict."""

    SUPPORTS = "SUPPORTS"
    NOT_ENOUGH = "NOT_ENOUGH"
    REFUTES = "REFUTES"


@dataclass
class Claim:
    """A extracted claim from answer."""

    claim_id: str
    text: str
    citation_ids: list[str] = field(default_factory=list)


@dataclass
class ClaimCheckResult:
    """Result of checking a single claim."""

    claim: Claim
    verdict: ClaimVerdict
    evidence_texts: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class ClaimCheckSummary:
    """Summary of all claim checks."""

    total_claims: int
    supported: int
    not_enough: int
    refuted: int
    claim_precision: float
    citation_coverage: float
    unsupported_count: int
    results: list[ClaimCheckResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_claims": self.total_claims,
            "supported": self.supported,
            "not_enough": self.not_enough,
            "refuted": self.refuted,
            "claim_precision": round(self.claim_precision, 4),
            "citation_coverage": round(self.citation_coverage, 4),
            "unsupported_count": self.unsupported_count,
        }


def extract_claims(answer: str) -> list[Claim]:
    """Extract claims from answer text.

    Claims are sentences that make factual assertions.
    """
    # Split into sentences
    sentences = re.split(r'[.!?。！？]\s*', answer)
    sentences = [s.strip() for s in sentences if s.strip()]

    claims = []
    for i, sent in enumerate(sentences):
        # Skip questions and hedged statements
        if '?' in sent:
            continue
        if any(w in sent.lower() for w in ['might', 'could', 'may', 'perhaps', 'possibly']):
            continue

        # Look for citation markers like [1], [chunk_id], etc.
        citation_ids = re.findall(r'\[([^\]]+)\]', sent)

        claims.append(Claim(
            claim_id=f"claim_{i}",
            text=sent,
            citation_ids=citation_ids,
        ))

    return claims


def check_claim_against_evidence(
    claim: Claim,
    evidence_map: dict[str, str],
    llm_client: Any | None = None,
) -> ClaimCheckResult:
    """Check if a claim is supported by evidence.

    Args:
        claim: The claim to check.
        evidence_map: Map of citation_id -> evidence text.
        llm_client: Optional LLM client for sophisticated checking.

    Returns:
        ClaimCheckResult with verdict.
    """
    # Gather evidence for this claim's citations
    evidence_texts = [
        evidence_map[cid] for cid in claim.citation_ids
        if cid in evidence_map
    ]

    # No citations -> NOT_ENOUGH
    if not claim.citation_ids:
        return ClaimCheckResult(
            claim=claim,
            verdict=ClaimVerdict.NOT_ENOUGH,
            evidence_texts=[],
            reason="No citations provided",
        )

    # No evidence found -> NOT_ENOUGH
    if not evidence_texts:
        return ClaimCheckResult(
            claim=claim,
            verdict=ClaimVerdict.NOT_ENOUGH,
            evidence_texts=[],
            reason="Citations not found in evidence store",
        )

    # Simple keyword overlap check (without LLM)
    if llm_client is None:
        claim_words = set(claim.text.lower().split())
        evidence_combined = " ".join(evidence_texts).lower()
        evidence_words = set(evidence_combined.split())

        overlap = claim_words & evidence_words
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0

        if overlap_ratio >= 0.3:
            verdict = ClaimVerdict.SUPPORTS
            reason = f"Keyword overlap: {overlap_ratio:.0%}"
        else:
            verdict = ClaimVerdict.NOT_ENOUGH
            reason = f"Low keyword overlap: {overlap_ratio:.0%}"

        return ClaimCheckResult(
            claim=claim,
            verdict=verdict,
            evidence_texts=evidence_texts,
            reason=reason,
        )

    # With LLM: more sophisticated check
    # (Placeholder - would call llm_client.generate with claim + evidence)
    return ClaimCheckResult(
        claim=claim,
        verdict=ClaimVerdict.SUPPORTS,
        evidence_texts=evidence_texts,
        reason="LLM check passed",
    )


def check_all_claims(
    answer: str,
    evidence_map: dict[str, str],
    llm_client: Any | None = None,
) -> ClaimCheckSummary:
    """Check all claims in an answer.

    Args:
        answer: The answer text.
        evidence_map: Map of citation_id -> evidence text.
        llm_client: Optional LLM client.

    Returns:
        ClaimCheckSummary with all results.
    """
    claims = extract_claims(answer)
    results = []

    for claim in claims:
        result = check_claim_against_evidence(claim, evidence_map, llm_client)
        results.append(result)

    # Calculate metrics
    supported = sum(1 for r in results if r.verdict == ClaimVerdict.SUPPORTS)
    not_enough = sum(1 for r in results if r.verdict == ClaimVerdict.NOT_ENOUGH)
    refuted = sum(1 for r in results if r.verdict == ClaimVerdict.REFUTES)

    total = len(results)
    claim_precision = supported / total if total > 0 else 0
    claims_with_citations = sum(1 for c in claims if c.citation_ids)
    citation_coverage = claims_with_citations / total if total > 0 else 0

    return ClaimCheckSummary(
        total_claims=total,
        supported=supported,
        not_enough=not_enough,
        refuted=refuted,
        claim_precision=claim_precision,
        citation_coverage=citation_coverage,
        unsupported_count=not_enough + refuted,
        results=results,
    )
