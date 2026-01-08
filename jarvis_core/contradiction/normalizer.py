"""Claim Normalizer.

Normalizes claims for comparison.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.3.1
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from jarvis_core.contradiction.schema import Claim

logger = logging.getLogger(__name__)


# Patterns for extracting claim components
EFFECT_PATTERNS = [
    # Increase/decrease patterns
    re.compile(r'\b(increase[sd]?|decrease[sd]?|reduce[sd]?|improve[sd]?|worsen[sd]?)\s+(.+?)(?:\s+by|\s+in|\.|$)', re.IGNORECASE),
    # Association patterns
    re.compile(r'\b(associated\s+with|correlate[sd]?\s+with|linked\s+to)\s+(.+?)(?:\s+in|\.|$)', re.IGNORECASE),
    # Causation patterns
    re.compile(r'\b(cause[sd]?|lead[s]?\s+to|result[s]?\s+in)\s+(.+?)(?:\s+in|\.|$)', re.IGNORECASE),
]

NEGATION_PATTERNS = [
    re.compile(r'\b(no|not|neither|nor|never|without|lacks?|absent|fail(?:ed|s)?)\b', re.IGNORECASE),
    re.compile(r'\b(does\s+not|did\s+not|do\s+not|cannot|could\s+not)\b', re.IGNORECASE),
]

QUANTITATIVE_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*(%|percent|fold|times|mg|kg|ml|μg|ng|mmol|μmol)',
    re.IGNORECASE
)


@dataclass
class NormalizationResult:
    """Result of claim normalization."""

    original: str
    normalized: str
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    qualifier: str | None = None
    is_negated: bool = False
    quantities: list[tuple[float, str]] = None

    def __post_init__(self):
        if self.quantities is None:
            self.quantities = []


class ClaimNormalizer:
    """Normalizes claims for comparison.
    
    Extracts structured components and creates normalized forms
    to enable contradiction detection.
    
    Example:
        >>> normalizer = ClaimNormalizer()
        >>> result = normalizer.normalize("Drug X increases survival by 20%")
        >>> print(result.predicate)
        'increases'
    """

    def __init__(self):
        """Initialize the normalizer."""
        self._effect_patterns = EFFECT_PATTERNS
        self._negation_patterns = NEGATION_PATTERNS
        self._quantity_pattern = QUANTITATIVE_PATTERN

    def normalize(self, claim_text: str) -> NormalizationResult:
        """Normalize a claim text.
        
        Args:
            claim_text: Raw claim text
            
        Returns:
            NormalizationResult with structured components
        """
        if not claim_text:
            return NormalizationResult(original="", normalized="")

        # Clean text
        text = self._clean_text(claim_text)

        # Detect negation
        is_negated = self._detect_negation(text)

        # Extract quantities
        quantities = self._extract_quantities(text)

        # Extract semantic components
        subject, predicate, obj = self._extract_components(text)

        # Create normalized form
        normalized = self._create_normalized_form(
            subject, predicate, obj, is_negated
        )

        return NormalizationResult(
            original=claim_text,
            normalized=normalized,
            subject=subject,
            predicate=predicate,
            object=obj,
            is_negated=is_negated,
            quantities=quantities,
        )

    def normalize_claim(self, claim: Claim) -> Claim:
        """Normalize a Claim object in-place.
        
        Args:
            claim: Claim to normalize
            
        Returns:
            The same Claim with normalized fields populated
        """
        result = self.normalize(claim.text)

        claim.normalized_text = result.normalized
        claim.subject = result.subject
        claim.predicate = result.predicate
        claim.object = result.object

        return claim

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove citation markers
        text = re.sub(r'\[\d+(?:[-,]\d+)*\]', '', text)
        text = re.sub(r'\([A-Z][a-z]+\s+et\s+al\.?,?\s*\d{4}\)', '', text)
        return text.strip()

    def _detect_negation(self, text: str) -> bool:
        """Detect if the claim is negated."""
        for pattern in self._negation_patterns:
            if pattern.search(text):
                return True
        return False

    def _extract_quantities(self, text: str) -> list[tuple[float, str]]:
        """Extract quantitative values from text."""
        quantities = []
        for match in self._quantity_pattern.finditer(text):
            try:
                value = float(match.group(1))
                unit = match.group(2).lower()
                quantities.append((value, unit))
            except ValueError:
                pass
        return quantities

    def _extract_components(self, text: str) -> tuple[str | None, str | None, str | None]:
        """Extract subject, predicate, object from text."""
        subject = None
        predicate = None
        obj = None

        for pattern in self._effect_patterns:
            match = pattern.search(text)
            if match:
                predicate = match.group(1).lower()
                obj = match.group(2).strip()

                # Try to extract subject (text before the predicate)
                pre_match = text[:match.start()].strip()
                if pre_match:
                    # Take last significant phrase as subject
                    subject = self._extract_subject(pre_match)
                break

        return subject, predicate, obj

    def _extract_subject(self, text: str) -> str | None:
        """Extract subject from pre-predicate text."""
        # Remove common prefixes
        text = re.sub(r'^(the|a|an|this|that|these|those)\s+', '', text, flags=re.IGNORECASE)

        # Take last noun phrase (simplified)
        words = text.split()
        if words:
            return ' '.join(words[-3:]) if len(words) > 3 else text
        return None

    def _create_normalized_form(
        self,
        subject: str | None,
        predicate: str | None,
        obj: str | None,
        is_negated: bool,
    ) -> str:
        """Create normalized form from components."""
        parts = []

        if subject:
            parts.append(subject.lower())

        if predicate:
            if is_negated:
                parts.append(f"NOT:{predicate}")
            else:
                parts.append(predicate)

        if obj:
            parts.append(obj.lower())

        return " | ".join(parts) if parts else ""

    def are_about_same_topic(self, claim_a: Claim, claim_b: Claim) -> bool:
        """Check if two claims are about the same topic.
        
        Args:
            claim_a: First claim
            claim_b: Second claim
            
        Returns:
            True if claims appear to be about the same topic
        """
        # Normalize if needed
        if not claim_a.normalized_text:
            self.normalize_claim(claim_a)
        if not claim_b.normalized_text:
            self.normalize_claim(claim_b)

        # Check subject overlap
        if claim_a.subject and claim_b.subject:
            subject_a = set(claim_a.subject.lower().split())
            subject_b = set(claim_b.subject.lower().split())
            if subject_a & subject_b:
                return True

        # Check object overlap
        if claim_a.object and claim_b.object:
            obj_a = set(claim_a.object.lower().split())
            obj_b = set(claim_b.object.lower().split())
            if obj_a & obj_b:
                return True

        return False
