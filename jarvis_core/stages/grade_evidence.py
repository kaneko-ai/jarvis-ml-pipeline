"""Evidence Grading Stage.

Evaluates the strength of evidence for each claim.
Detects unsupported claims and assigns evidence strength grades.

Output: Updates evidence.jsonl with strength ratings
"""
from typing import Any, Dict, List
from jarvis_core.pipelines.stage_registry import register_stage
from jarvis_core.task import TaskContext, Artifacts


def calculate_evidence_strength(evidence: Dict, claim: Dict) -> str:
    """Calculate evidence strength based on multiple factors.
    
    Returns: "Strong" | "Medium" | "Weak" | "None"
    """
    # Simple heuristic for Phase 2 bootstrap
    # In production, this would use LLM or ML model
    
    quote_len = len(evidence.get("quote_span", ""))
    
    # Check if evidence is from the same paper as claim
    same_paper = evidence.get("paper_id") == claim.get("source_paper_id")
    
    # Check role
    role = evidence.get("evidence_role", "Direct")
    
    # Grading logic
    if role == "Direct" and same_paper and quote_len > 100:
        return "Strong"
    elif role == "Direct" and quote_len > 50:
        return "Medium"
    elif role in ["Indirect", "Prior"] and quote_len > 50:
        return "Medium"
    elif quote_len > 20:
        return "Weak"
    else:
        return "None"


@register_stage("quality_gate.evidence_grading")
def grade_evidence(context: TaskContext, artifacts: Artifacts) -> Dict[str, Any]:
    """Grade all evidence and calculate support rates."""
    
    claims = artifacts.get("claims", [])
    evidence_list = artifacts.get("evidence", [])
    
    # Build evidence map: claim_id -> [evidence]
    evidence_by_claim = {}
    for ev in evidence_list:
        claim_id = ev.get("claim_id")
        if claim_id not in evidence_by_claim:
            evidence_by_claim[claim_id] = []
        evidence_by_claim[claim_id].append(ev)
    
    # Grade each claim's evidence
    unsupported_claims = []
    weakly_supported = []
    
    for claim in claims:
        claim_id = claim["claim_id"]
        evidences = evidence_by_claim.get(claim_id, [])
        
        if not evidences:
            unsupported_claims.append(claim)
            continue
        
        # Calculate aggregate strength
        strengths = []
        for ev in evidences:
            # Re-grade based on claim context
            strength = calculate_evidence_strength(ev, claim)
            ev["evidence_strength"] = strength  # Update in-place
            strengths.append(strength)
        
        # Check if at least one Strong or two Medium
        has_strong = "Strong" in strengths
        medium_count = strengths.count("Medium")
        
        if not has_strong and medium_count < 2:
            weakly_supported.append(claim)
    
    # Update artifacts with graded evidence
    artifacts["evidence"] = evidence_list
    
    # Calculate metrics
    total_claims = len(claims)
    supported_claims = total_claims - len(unsupported_claims)
    support_rate = supported_claims / total_claims if total_claims > 0 else 0.0
    
    # Store grading summary in artifacts for downstream use
    artifacts["evidence_grading_summary"] = {
        "total_claims": total_claims,
        "supported_claims": supported_claims,
        "unsupported_claims": len(unsupported_claims),
        "weakly_supported": len(weakly_supported),
        "support_rate": support_rate
    }
    
    # Provenance
    context.provenance.add("evidence.jsonl", "quality_gate.evidence_grading")
    
    return {
        "support_rate": support_rate,
        "unsupported_count": len(unsupported_claims),
        "weakly_supported_count": len(weakly_supported),
        "gate_pass": len(unsupported_claims) == 0 and support_rate >= 0.90
    }
