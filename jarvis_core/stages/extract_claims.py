"""Claim Extraction Stage (Phase 2).

Extracts atomic claims from papers into structured Claim Units.
Each claim conforms to docs/SCHEMAS/claim_unit.schema.json.

Output: claims.jsonl (one claim per line)
"""

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def extract_claims(papers: list[dict], **kwargs) -> dict[str, Any]:
    """Extract atomic claims from papers.

    In production, this would use LLM to extract claims.
    For Phase 2 bootstrap, we use simple heuristics.

    Args:
        papers: List of paper dictionaries
        **kwargs: Additional context (task_id, etc.)

    Returns:
        Dict with 'claims' list and metadata
    """
    claims = []

    for paper in papers[:5]:  # Process first 5 papers for demo
        paper_id = paper.get("paper_id", f"paper_{uuid.uuid4().hex[:8]}")
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")

        # Simple heuristic: extract sentences as claims
        # In production, use LLM with prompt engineering
        text = f"{title}. {abstract}"
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]

        for i, sentence in enumerate(sentences[:3]):  # Max 3 claims per paper
            claim_id = f"claim_{uuid.uuid4().hex[:12]}"

            claim = {
                "claim_id": claim_id,
                "claim_text": sentence,
                "claim_type": "Mechanism" if i == 0 else "Observation",
                "source_paper_id": paper_id,
                "confidence_self": 0.7,
                "entity": {"type": "protein", "name": "CD73"},  # Example
            }
            claims.append(claim)

    logger.info(f"Extracted {len(claims)} claims from {len(papers)} papers")

    return {
        "claims": claims,
        "count": len(claims),
        "stage": "extraction.claims",
        "source_papers": len(papers),
    }