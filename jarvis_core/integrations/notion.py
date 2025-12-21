"""Notion exporter for Evidence Bundle.

Exports a JSON structure that can be imported into Notion
or used for sharing/review purposes.

Per RP19, this creates a structured JSON for Notion DB import.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..result import EvidenceQAResult
    from ..reference import Reference


def export_notion(
    result: "EvidenceQAResult",
    references: List["Reference"],
) -> str:
    """Export Evidence Bundle for Notion.

    Creates a JSON structure compatible with Notion's
    database structure expectations.

    Args:
        result: The EvidenceQAResult.
        references: List of extracted references.

    Returns:
        JSON string for Notion import.
    """
    # Build claims data
    claims_data = []
    if result.claims is not None:
        for claim in result.claims.claims:
            # Find references for this claim
            claim_refs = []
            for ref in references:
                if any(cid in claim.citations for cid in ref.chunk_ids):
                    claim_refs.append(ref.get_display_locator())

            claims_data.append({
                "id": claim.id,
                "text": claim.text,
                "valid": claim.valid,
                "references": claim_refs,
            })

    # Build references data
    refs_data = []
    for ref in references:
        refs_data.append({
            "id": ref.id,
            "type": ref.source_type,
            "locator": ref.get_display_locator(),
            "title": ref.title,
            "authors": ref.authors,
            "year": ref.year,
            "pages": ref.get_pages_display(),
        })

    # Build the complete export
    export_data = {
        "type": "jarvis_evidence_export",
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "query": result.query,
        "answer": result.answer,
        "status": result.status,
        "claims": claims_data,
        "references": refs_data,
        "stats": {
            "total_claims": len(claims_data),
            "valid_claims": sum(1 for c in claims_data if c["valid"]),
            "total_references": len(refs_data),
            "total_citations": len(result.citations),
        },
    }

    return json.dumps(export_data, indent=2, ensure_ascii=False)
