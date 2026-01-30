"""Counter Evidence Search (Phase 2-ΩΩ P2).

Actively searches for disconfirming evidence to prevent confirmation bias.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def find_counter_evidence(claim: dict[str, Any], papers: list[dict], **kwargs) -> list[dict]:
    """Find evidence that refutes or contradicts a claim.

    Args:
        claim: Claim dictionary
        papers: List of paper dictionaries
        **kwargs: Additional context

    Returns:
        List of counter-evidence dictionaries
    """
    counter_evidence = []
    claim_id = claim.get("claim_id", "")
    claim.get("claim_text", "")

    # Simple heuristic: look for negation patterns
    # In production, use LLM with "find contradicting evidence" prompt

    for paper in papers[:5]:  # Limit search
        paper_id = paper.get("paper_id", "")
        abstract = paper.get("abstract", "").lower()

        # Look for contradiction keywords
        contradiction_patterns = [
            "however",
            "contradicts",
            "in contrast",
            "opposite",
            "no evidence",
            "failed to show",
        ]

        has_contradiction = any(pattern in abstract for pattern in contradiction_patterns)

        if has_contradiction:
            # Mock counter evidence
            import uuid

            evidence_id = f"counter_ev_{uuid.uuid4().hex[:12]}"

            counter_ev = {
                "evidence_id": evidence_id,
                "claim_id": claim_id,
                "paper_id": paper_id,
                "evidence_role": "refuting",  # Not "supporting"
                "quote_span": f"[Contradictory finding in {paper_id}]",
                "locator": {"page": 1, "paragraph": 1},
                "evidence_strength": "Medium",
            }

            counter_evidence.append(counter_ev)

    logger.info(f"Found {len(counter_evidence)} counter-evidence for claim {claim_id}")

    return counter_evidence


def merge_supporting_and_refuting(supporting: list[dict], refuting: list[dict]) -> dict[str, Any]:
    """Merge supporting and refuting evidence for balanced view.

    Args:
        supporting: List of supporting evidence
        refuting: List of refuting evidence

    Returns:
        Dict with 'conclusion_type', 'synthesis'
    """
    support_count = len(supporting)
    refute_count = len(refuting)

    if refute_count == 0:
        conclusion_type = "supported"
        synthesis = f"Supported by {support_count} evidence"
    elif support_count == 0:
        conclusion_type = "refuted"
        synthesis = f"Refuted by {refute_count} evidence"
    else:
        conclusion_type = "conflicting"
        synthesis = f"Conflicting evidence: {support_count} support vs {refute_count} refute"

    return {
        "conclusion_type": conclusion_type,
        "synthesis": synthesis,
        "support_count": support_count,
        "refute_count": refute_count,
    }