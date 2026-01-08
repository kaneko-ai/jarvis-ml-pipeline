"""Artifacts package."""
from .claim_set import Claim, ClaimSet, ClaimType
from .schema import (
    ArtifactBase,
    EvidenceRef,
    Fact,
    Inference,
    Provenance,
    Recommendation,
    TruthLevel,
    create_artifact,
)

__all__ = [
    "ArtifactBase",
    "Fact",
    "Inference",
    "Recommendation",
    "EvidenceRef",
    "Provenance",
    "TruthLevel",
    "create_artifact",
    "ClaimSet",
    "Claim",
    "ClaimType",
]

