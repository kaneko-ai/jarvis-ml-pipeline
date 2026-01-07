"""Contradiction Detector.

Detects contradictions between claims.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.3.2-2.3.3
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jarvis_core.contradiction.schema import (
    Claim,
    ClaimPair,
    ContradictionResult,
    ContradictionType,
)
from jarvis_core.contradiction.normalizer import ClaimNormalizer

logger = logging.getLogger(__name__)


# Antonym pairs for contradiction detection
ANTONYM_PAIRS = [
    ("increase", "decrease"),
    ("improve", "worsen"),
    ("higher", "lower"),
    ("more", "less"),
    ("positive", "negative"),
    ("significant", "insignificant"),
    ("effective", "ineffective"),
    ("beneficial", "harmful"),
    ("safe", "unsafe"),
    ("associated", "not associated"),
]


@dataclass
class DetectionConfig:
    """Configuration for contradiction detection."""
    
    similarity_threshold: float = 0.7  # Min similarity to consider
    negation_weight: float = 2.0       # Weight for negation contradictions
    antonym_weight: float = 1.5        # Weight for antonym contradictions
    quantity_tolerance: float = 0.2    # Tolerance for quantity comparisons
    use_embeddings: bool = True        # Use embeddings for similarity


class ContradictionDetector:
    """Detects contradictions between claims.
    
    Uses multiple signals:
    - Negation patterns
    - Antonym detection
    - Quantitative differences
    - Semantic similarity
    
    Example:
        >>> detector = ContradictionDetector()
        >>> result = detector.detect(claim_a, claim_b)
        >>> if result.is_contradictory:
        ...     print(f"Contradiction: {result.explanation}")
    """
    
    def __init__(self, config: Optional[DetectionConfig] = None):
        """Initialize the detector.
        
        Args:
            config: Detection configuration
        """
        self._config = config or DetectionConfig()
        self._normalizer = ClaimNormalizer()
        self._embedder = None
        
        # Build antonym lookup
        self._antonyms: Dict[str, str] = {}
        for a, b in ANTONYM_PAIRS:
            self._antonyms[a] = b
            self._antonyms[b] = a
    
    def detect(self, claim_a: Claim, claim_b: Claim) -> ContradictionResult:
        """Detect contradiction between two claims.
        
        Args:
            claim_a: First claim
            claim_b: Second claim
            
        Returns:
            ContradictionResult with detection results
        """
        # Normalize claims if needed
        if not claim_a.normalized_text:
            self._normalizer.normalize_claim(claim_a)
        if not claim_b.normalized_text:
            self._normalizer.normalize_claim(claim_b)
        
        # Check if claims are about the same topic
        if not self._normalizer.are_about_same_topic(claim_a, claim_b):
            return ContradictionResult(
                claim_pair=ClaimPair(claim_a, claim_b),
                contradiction_type=ContradictionType.NONE,
                confidence=0.0,
                explanation="Claims are not about the same topic",
            )
        
        # Calculate similarity (if embeddings available)
        similarity = self._calculate_similarity(claim_a, claim_b)
        
        # Check various contradiction types
        scores: Dict[str, float] = {}
        evidence: List[str] = []
        
        # Check negation contradiction
        neg_score, neg_evidence = self._check_negation(claim_a, claim_b)
        scores["negation"] = neg_score
        if neg_evidence:
            evidence.append(neg_evidence)
        
        # Check antonym contradiction
        ant_score, ant_evidence = self._check_antonyms(claim_a, claim_b)
        scores["antonym"] = ant_score
        if ant_evidence:
            evidence.append(ant_evidence)
        
        # Check quantitative contradiction
        quant_score, quant_evidence = self._check_quantitative(claim_a, claim_b)
        scores["quantitative"] = quant_score
        if quant_evidence:
            evidence.append(quant_evidence)
        
        # Determine overall contradiction type and confidence
        contradiction_type, confidence = self._determine_contradiction(scores)
        
        # Build explanation
        explanation = self._build_explanation(
            claim_a, claim_b, contradiction_type, evidence
        )
        
        return ContradictionResult(
            claim_pair=ClaimPair(claim_a, claim_b, similarity),
            contradiction_type=contradiction_type,
            confidence=confidence,
            explanation=explanation,
            evidence=evidence,
            scores=scores,
        )
    
    def detect_all(
        self,
        claims: List[Claim],
        filter_same_paper: bool = True,
    ) -> List[ContradictionResult]:
        """Detect contradictions among multiple claims.
        
        Args:
            claims: List of claims to compare
            filter_same_paper: Exclude comparisons within same paper
            
        Returns:
            List of ContradictionResult for contradictory pairs
        """
        results = []
        
        for i, claim_a in enumerate(claims):
            for claim_b in claims[i + 1:]:
                # Skip same-paper comparisons if requested
                if filter_same_paper and claim_a.paper_id == claim_b.paper_id:
                    continue
                
                result = self.detect(claim_a, claim_b)
                if result.is_contradictory:
                    results.append(result)
        
        # Sort by confidence
        results.sort(key=lambda r: r.confidence, reverse=True)
        
        return results
    
    def _calculate_similarity(self, claim_a: Claim, claim_b: Claim) -> float:
        """Calculate semantic similarity between claims."""
        if not self._config.use_embeddings:
            return 0.0
        
        # Use pre-computed embeddings if available
        if claim_a.embedding and claim_b.embedding:
            return self._cosine_similarity(claim_a.embedding, claim_b.embedding)
        
        # Try to get embeddings
        if self._embedder is None:
            try:
                from jarvis_core.embeddings import SentenceTransformerEmbedding
                self._embedder = SentenceTransformerEmbedding()
            except ImportError:
                return 0.0
        
        try:
            embeddings = self._embedder.encode([claim_a.text, claim_b.text])
            return self._cosine_similarity(
                embeddings[0].tolist(),
                embeddings[1].tolist()
            )
        except Exception:
            return 0.0
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot / (norm_a * norm_b)
    
    def _check_negation(
        self,
        claim_a: Claim,
        claim_b: Claim
    ) -> Tuple[float, Optional[str]]:
        """Check for negation-based contradiction."""
        # Check if predicates are the same but one is negated
        if claim_a.predicate and claim_b.predicate:
            pred_a = claim_a.predicate.lower()
            pred_b = claim_b.predicate.lower()
            
            # Check normalized text for NOT: prefix
            norm_a = claim_a.normalized_text or ""
            norm_b = claim_b.normalized_text or ""
            
            a_negated = "NOT:" in norm_a
            b_negated = "NOT:" in norm_b
            
            # Same predicate but different negation
            if pred_a == pred_b and a_negated != b_negated:
                return (
                    self._config.negation_weight,
                    f"Predicate '{pred_a}' negated in one claim"
                )
        
        return 0.0, None
    
    def _check_antonyms(
        self,
        claim_a: Claim,
        claim_b: Claim
    ) -> Tuple[float, Optional[str]]:
        """Check for antonym-based contradiction."""
        if claim_a.predicate and claim_b.predicate:
            pred_a = claim_a.predicate.lower()
            pred_b = claim_b.predicate.lower()
            
            # Check if predicates are antonyms
            if self._antonyms.get(pred_a) == pred_b:
                return (
                    self._config.antonym_weight,
                    f"Antonym predicates: '{pred_a}' vs '{pred_b}'"
                )
        
        # Check in full text for antonym pairs
        text_a = claim_a.text.lower()
        text_b = claim_b.text.lower()
        
        for word_a, word_b in ANTONYM_PAIRS:
            if word_a in text_a and word_b in text_b:
                return (
                    self._config.antonym_weight * 0.5,
                    f"Antonyms found: '{word_a}' vs '{word_b}'"
                )
        
        return 0.0, None
    
    def _check_quantitative(
        self,
        claim_a: Claim,
        claim_b: Claim
    ) -> Tuple[float, Optional[str]]:
        """Check for quantitative contradiction."""
        # Get quantities from normalized results
        result_a = self._normalizer.normalize(claim_a.text)
        result_b = self._normalizer.normalize(claim_b.text)
        
        if not result_a.quantities or not result_b.quantities:
            return 0.0, None
        
        # Compare quantities with same units
        for val_a, unit_a in result_a.quantities:
            for val_b, unit_b in result_b.quantities:
                if unit_a == unit_b:
                    # Check for significant difference
                    if val_a == 0 or val_b == 0:
                        continue
                    
                    ratio = abs(val_a - val_b) / max(val_a, val_b)
                    if ratio > self._config.quantity_tolerance:
                        return (
                            min(2.0, ratio * 2),
                            f"Quantitative difference: {val_a}{unit_a} vs {val_b}{unit_b}"
                        )
        
        return 0.0, None
    
    def _determine_contradiction(
        self,
        scores: Dict[str, float]
    ) -> Tuple[ContradictionType, float]:
        """Determine contradiction type and confidence from scores."""
        max_score = max(scores.values()) if scores else 0.0
        
        if max_score >= self._config.negation_weight:
            if scores.get("negation", 0) >= self._config.negation_weight:
                return ContradictionType.DIRECT, min(1.0, max_score / 2)
            elif scores.get("antonym", 0) >= self._config.antonym_weight:
                return ContradictionType.DIRECT, min(1.0, max_score / 2)
        
        if scores.get("quantitative", 0) > 0.5:
            return ContradictionType.QUANTITATIVE, min(1.0, scores["quantitative"] / 2)
        
        if max_score > 0.5:
            return ContradictionType.PARTIAL, min(1.0, max_score / 3)
        
        return ContradictionType.NONE, 0.0
    
    def _build_explanation(
        self,
        claim_a: Claim,
        claim_b: Claim,
        contradiction_type: ContradictionType,
        evidence: List[str],
    ) -> str:
        """Build explanation for the contradiction."""
        if contradiction_type == ContradictionType.NONE:
            return "No contradiction detected"
        
        parts = [f"Contradiction type: {contradiction_type.value}"]
        
        if evidence:
            parts.append("Evidence: " + "; ".join(evidence))
        
        return " | ".join(parts)


def detect_contradiction(claim_a: Claim, claim_b: Claim) -> ContradictionResult:
    """Detect contradiction between two claims.
    
    Convenience function for quick detection.
    
    Args:
        claim_a: First claim
        claim_b: Second claim
        
    Returns:
        ContradictionResult
    """
    detector = ContradictionDetector()
    return detector.detect(claim_a, claim_b)
