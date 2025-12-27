"""Claim Extraction Stage.

Performs atomic claim extraction from papers.
Output: claims.jsonl (Phase 2 Claim Unit Schema)
"""
from typing import Any, Dict, List
import uuid

from jarvis_core.pipelines.stage_registry import register_stage
from jarvis_core.task import TaskContext, Artifacts


@register_stage("extraction.claims")
def extract_claims(context: TaskContext, artifacts: Artifacts) -> Dict[str, Any]:
    """Extract atomic claims from papers."""
    claims = []
    papers = artifacts.get("papers", [])
    
    # Mock implementation for Phase 2 bootstrap
    # In real implementation, this would use LLM to extract claims
    
    for paper in papers:
        # Example extraction logic (simple splitting for now)
        abstract = paper.get("abstract", "")
        sentences = [s.strip() for s in abstract.split(". ") if s.strip()]
        
        for i, sentence in enumerate(sentences):
            if len(sentence) < 20:
                continue
                
            claim = {
                "claim_id": str(uuid.uuid4()),
                "claim_text": sentence,
                "claim_type": "Unknown",  # To be classified
                "entity": paper.get("query", "Unknown"),
                "scope": "unknown",
                "polarity": "neutral",
                "source_paper_id": paper.get("paper_id", ""),
                "source_locator": {
                    "section": "abstract",
                    "sentence_index": i
                },
                "confidence_self": 0.8  # Mock confidence
            }
            claims.append(claim)
            
    # Update artifacts
    artifacts["claims"] = claims
    
    # Provenance update
    context.provenance.add("claims.jsonl", "extraction.claims")
    
    return {
        "count": len(claims),
        "source_papers": len(papers)
    }
