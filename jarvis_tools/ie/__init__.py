"""Information Extraction tools."""
from .evidence_extractor import (
    EvidenceExtractor,
    Evidence,
    Locator,
    ExtractionResult,
    extract_evidence,
)
from .claim_extractor import (
    ClaimExtractor,
    Claim,
    ExtractionResult as ClaimExtractionResult,
    extract_claims,
)

__all__ = [
    "EvidenceExtractor",
    "Evidence",
    "Locator",
    "ExtractionResult",
    "extract_evidence",
    "ClaimExtractor",
    "Claim",
    "ClaimExtractionResult",
    "extract_claims",
]

