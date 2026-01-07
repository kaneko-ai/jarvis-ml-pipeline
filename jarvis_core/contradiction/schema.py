"""Contradiction Detection Schema.

Data structures for contradiction detection.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ContradictionType(Enum):
    """Types of contradictions between claims."""
    
    DIRECT = "direct"           # A says X, B says not X
    QUANTITATIVE = "quantitative"  # Different numeric values
    TEMPORAL = "temporal"       # Different time periods/results
    METHODOLOGICAL = "methodological"  # Different methods lead to different conclusions
    PARTIAL = "partial"         # Partially overlapping contradictions
    NONE = "none"               # No contradiction
    UNCERTAIN = "uncertain"     # Cannot determine


@dataclass
class Claim:
    """A scientific claim extracted from a paper."""
    
    claim_id: str
    text: str
    paper_id: str
    
    # Normalized form for comparison
    normalized_text: Optional[str] = None
    
    # Optional metadata
    section: Optional[str] = None
    confidence: float = 1.0
    
    # Semantic components (PICO-like)
    subject: Optional[str] = None      # What is being studied
    predicate: Optional[str] = None    # Relationship/action
    object: Optional[str] = None       # Effect/outcome
    qualifier: Optional[str] = None    # Conditions/modifiers
    
    # Embedding for similarity comparison
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "paper_id": self.paper_id,
            "normalized_text": self.normalized_text,
            "section": self.section,
            "confidence": self.confidence,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "qualifier": self.qualifier,
        }


@dataclass
class ClaimPair:
    """A pair of claims to compare for contradiction."""
    
    claim_a: Claim
    claim_b: Claim
    similarity_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "claim_a": self.claim_a.to_dict(),
            "claim_b": self.claim_b.to_dict(),
            "similarity_score": self.similarity_score,
        }


@dataclass
class ContradictionResult:
    """Result of contradiction detection."""
    
    claim_pair: ClaimPair
    contradiction_type: ContradictionType
    confidence: float
    
    # Explanation of the contradiction
    explanation: str = ""
    
    # Evidence supporting the detection
    evidence: List[str] = field(default_factory=list)
    
    # Detailed scores
    scores: Dict[str, float] = field(default_factory=dict)
    
    @property
    def is_contradictory(self) -> bool:
        """Check if claims contradict."""
        return self.contradiction_type not in [
            ContradictionType.NONE,
            ContradictionType.UNCERTAIN,
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "claim_pair": self.claim_pair.to_dict(),
            "contradiction_type": self.contradiction_type.value,
            "confidence": self.confidence,
            "is_contradictory": self.is_contradictory,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "scores": self.scores,
        }
