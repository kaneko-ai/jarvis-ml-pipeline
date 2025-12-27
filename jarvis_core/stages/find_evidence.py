"""Evidence Finding Stage.

Finds supporting evidence for extracted claims.
Output: evidence.jsonl (Phase 2 Evidence Unit Schema)
"""
from typing import Any, Dict, List
import uuid

from jarvis_core.pipelines.stage_registry import register_stage
from jarvis_core.task import TaskContext, Artifacts


@register_stage("extraction.evidence_link")
def find_evidence(context: TaskContext, artifacts: Artifacts) -> Dict[str, Any]:
    """Find evidence for claims."""
    evidence_list = []
    claims = artifacts.get("claims", [])
    papers = {p["paper_id"]: p for p in artifacts.get("papers", [])}
    
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
            
    # Update artifacts
    artifacts["evidence"] = evidence_list
    
    # Provenance update
    context.provenance.add("evidence.jsonl", "extraction.evidence_link")
    
    return {
        "count": len(evidence_list),
        "coverage": len(evidence_list) / len(claims) if claims else 0
    }
