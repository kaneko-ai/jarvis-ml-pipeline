"""JARVIS Contradiction Detection Module.

Detects contradictions between research claims.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.3
"""

from jarvis_core.contradiction.detector import (
    ContradictionDetector,
    detect_contradiction,
)
from jarvis_core.contradiction.normalizer import ClaimNormalizer
from jarvis_core.contradiction.schema import (
    Claim,
    ClaimPair,
    ContradictionResult,
    ContradictionType,
)

__all__ = [
    "Claim",
    "ClaimPair",
    "ContradictionType",
    "ContradictionResult",
    "ContradictionDetector",
    "detect_contradiction",
    "ClaimNormalizer",
]