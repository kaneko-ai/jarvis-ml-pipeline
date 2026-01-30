"""FACT Evidence Enforcement.

Per V4-T01, this enforces that FACTs must have EvidenceRef.
FACTs without evidence are automatically downgraded to INFERENCE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.schema import ArtifactBase, Fact, Inference


def enforce_fact_evidence(
    facts: list[Fact],
) -> tuple[list[Fact], list[Inference], list[str]]:
    """Enforce evidence requirement on facts.

    Args:
        facts: List of facts to validate.

    Returns:
        Tuple of (valid_facts, downgraded_inferences, flags).
    """
    from ..artifacts.schema import Inference

    valid_facts = []
    downgraded = []
    flags = []

    for fact in facts:
        if fact.evidence_refs and len(fact.evidence_refs) > 0:
            # Valid fact with evidence
            valid_facts.append(fact)
        else:
            # Downgrade to inference
            inference = Inference(
                statement=f"[根拠不足により降格] {fact.statement}",
                method="evidence_enforcement_downgrade",
                confidence=0.3,
            )
            downgraded.append(inference)
            flags.append(f"Fact downgraded: '{fact.statement[:50]}...' (no evidence)")

    return valid_facts, downgraded, flags


def downgrade_to_inference(fact: Fact) -> Inference:
    """Downgrade a single fact to inference.

    Args:
        fact: Fact to downgrade.

    Returns:
        Inference with appropriate label.
    """
    from ..artifacts.schema import Inference

    return Inference(
        statement=f"[推定] {fact.statement}",
        method="downgrade_from_fact",
        confidence=min(fact.confidence * 0.5, 0.4),
    )


def enforce_artifact_truth(artifact: ArtifactBase) -> ArtifactBase:
    """Enforce truth requirements on an artifact.

    Args:
        artifact: Artifact to validate.

    Returns:
        Artifact with enforced truth levels.
    """
    valid_facts, downgraded, flags = enforce_fact_evidence(artifact.facts)

    # Add downgraded inferences
    new_inferences = list(artifact.inferences) + downgraded

    # Create new artifact with enforced facts
    from ..artifacts.schema import ArtifactBase

    return ArtifactBase(
        kind=artifact.kind,
        facts=valid_facts,
        inferences=new_inferences,
        recommendations=artifact.recommendations,
        metrics=artifact.metrics,
        confidence=artifact.confidence,
        provenance=artifact.provenance,
        raw_data={
            **artifact.raw_data,
            "truth_enforcement_flags": flags,
        },
    )
