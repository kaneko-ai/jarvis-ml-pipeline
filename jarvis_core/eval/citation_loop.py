"""Citation补充 Loop.

Per RP-127, automatically adds citations when min threshold not met.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class LoopStatus(Enum):
    """Status of citation補完ループ."""

    SUCCESS = "success"
    PARTIAL = "partial"
    MAX_ATTEMPTS = "max_attempts"


@dataclass
class CitationLoopResult:
    """Result of citation補完ループ."""

    status: LoopStatus
    attempts: int
    initial_citations: int
    final_citations: int
    added_citations: list[str]


@dataclass
class CitationCheckResult:
    """Result of citation check."""

    claim_id: str
    claim_text: str
    citation_count: int
    needs_more: bool


def check_citations(
    claims: list[dict],
    min_citations: int = 1,
) -> list[CitationCheckResult]:
    """Check which claims need more citations.

    Args:
        claims: List of claim dicts with 'id', 'text', 'citations'.
        min_citations: Minimum required citations per claim.

    Returns:
        List of CitationCheckResult for claims needing citations.
    """
    results = []

    for claim in claims:
        citations = claim.get("citations", [])
        count = len(citations)
        needs_more = count < min_citations

        results.append(CitationCheckResult(
            claim_id=claim.get("id", "unknown"),
            claim_text=claim.get("text", ""),
            citation_count=count,
            needs_more=needs_more,
        ))

    return results


def run_citation_loop(
    claims: list[dict],
    retrieve_fn: Callable[[str], list[dict]],
    min_citations: int = 1,
    max_attempts: int = 3,
) -> CitationLoopResult:
    """Run citation補充ループ.

    Adds citations to claims that don't meet minimum threshold.

    Args:
        claims: List of claim dicts.
        retrieve_fn: Function to retrieve citations for a claim text.
        min_citations: Minimum citations per claim.
        max_attempts: Maximum retrieval attempts.

    Returns:
        CitationLoopResult with status and metrics.
    """
    initial_total = sum(len(c.get("citations", [])) for c in claims)
    added = []

    for attempt in range(max_attempts):
        # Find claims needing citations
        checks = check_citations(claims, min_citations)
        needing = [c for c in checks if c.needs_more]

        if not needing:
            # All claims have enough citations
            final_total = sum(len(c.get("citations", [])) for c in claims)
            return CitationLoopResult(
                status=LoopStatus.SUCCESS,
                attempts=attempt + 1,
                initial_citations=initial_total,
                final_citations=final_total,
                added_citations=added,
            )

        # Try to add citations
        for check in needing:
            # Find the claim
            claim = next(
                (c for c in claims if c.get("id") == check.claim_id),
                None,
            )
            if not claim:
                continue

            # Retrieve new citations
            try:
                new_citations = retrieve_fn(check.claim_text)
                if new_citations:
                    existing = set(claim.get("citations", []))
                    for cit in new_citations:
                        cit_id = cit.get("id", str(cit))
                        if cit_id not in existing:
                            claim.setdefault("citations", []).append(cit_id)
                            added.append(cit_id)
                            existing.add(cit_id)
            except Exception:
                continue

    # Max attempts reached
    final_total = sum(len(c.get("citations", [])) for c in claims)
    still_needing = sum(1 for c in check_citations(claims, min_citations) if c.needs_more)

    status = LoopStatus.PARTIAL if still_needing > 0 else LoopStatus.SUCCESS

    return CitationLoopResult(
        status=status,
        attempts=max_attempts,
        initial_citations=initial_total,
        final_citations=final_total,
        added_citations=added,
    )
