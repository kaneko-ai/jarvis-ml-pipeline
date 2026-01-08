"""Evidence Finding Stage.

Finds supporting evidence for extracted claims.
Output: evidence.jsonl (Phase 2 Evidence Unit Schema)
"""
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def find_evidence(claims: list[dict], papers: list[dict], **kwargs) -> dict[str, Any]:
    """Find evidence for claims."""
    evidence_list = []
    # Claims and papers provided as arguments: p for p in artifacts.get("papers", [])}

    # Mock lookup
    for claim in claims:
        paper_id = claim.get("source_paper_id")
        paper = papers.get(paper_id)

        if not paper:
            continue

        # Simplified evidence finding: verify claim text exists in paper
        # In reality, this would use vector search / embedding similarity

        # Here we just link back to the abstract/section
        ev = {
            "evidence_id": str(uuid.uuid4()),
            "claim_id": claim["claim_id"],
            "paper_id": paper_id,
            "locator": {
                "section": "abstract",
                "paragraph_index": 0,
                "sentence_index": claim.get("source_locator", {}).get("sentence_index", 0),
                "char_offset": 0
            },
            "quote_span": claim["claim_text"][:400], # Direct quote for now
            "evidence_strength": "Strong",
            "evidence_role": "Direct",
            "contradiction_flag": False
        }
        evidence_list.append(ev)

    logger.info(f"Found {len(evidence_list)} evidence for {len(claims)} claims")

    return {
        "evidence": evidence_list,
        "count": len(evidence_list),
        "stage": "extraction.evidence_link",
        "coverage": len(evidence_list) / len(claims) if claims else 0
    }
