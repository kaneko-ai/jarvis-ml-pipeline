"""Unified Artifact Schema.

Per V4-A1, this defines the canonical contract for all module outputs.
All outputs must conform to ArtifactBase.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class TruthLevel(Enum):
    """Truthfulness layer classification."""

    FACT = "fact"          # Evidence-backed
    INFERENCE = "inference"  # Model/rule-derived, explicitly estimated
    RECOMMENDATION = "recommendation"  # Opinion/proposal


@dataclass
class EvidenceRef:
    """Reference to evidence chunk."""

    chunk_id: str
    source_locator: str
    text_snippet: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source_locator": self.source_locator,
            "text_snippet": self.text_snippet,
            "confidence": self.confidence,
        }


@dataclass
class Fact:
    """A fact backed by evidence. MUST have evidence_ref."""

    statement: str
    evidence_refs: list[EvidenceRef]
    confidence: float = 1.0

    def __post_init__(self):
        if not self.evidence_refs:
            raise ValueError("FACT must have at least one evidence_ref")

    def to_dict(self) -> dict:
        return {
            "type": "fact",
            "statement": self.statement,
            "evidence_refs": [e.to_dict() for e in self.evidence_refs],
            "confidence": self.confidence,
        }


@dataclass
class Inference:
    """An inference derived from model/rules. Explicitly marked as estimated."""

    statement: str
    method: str  # How it was derived
    confidence: float = 0.5
    supporting_facts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "inference",
            "statement": self.statement,
            "method": self.method,
            "confidence": self.confidence,
            "supporting_facts": self.supporting_facts,
            "estimated": True,
        }


@dataclass
class Recommendation:
    """A recommendation/opinion."""

    statement: str
    rationale: str
    priority: Literal["high", "medium", "low"] = "medium"
    confidence: float = 0.5

    def to_dict(self) -> dict:
        return {
            "type": "recommendation",
            "statement": self.statement,
            "rationale": self.rationale,
            "priority": self.priority,
            "confidence": self.confidence,
        }


@dataclass
class Provenance:
    """Tracks origin and lineage of artifact."""

    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "jarvis"
    version: str = "4.0"
    source_modules: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "version": self.version,
            "source_modules": self.source_modules,
            "parameters": self.parameters,
            "seed": self.seed,
        }


@dataclass
class ArtifactBase:
    """Base artifact following Canonical Contract.

    All module outputs should be convertible to this structure.
    """

    kind: str  # e.g., "gap_analysis", "grant_proposal", "hypothesis"
    facts: list[Fact] = field(default_factory=list)
    inferences: list[Inference] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)  # Normalized 0-1
    confidence: dict[str, float] = field(default_factory=dict)
    provenance: Provenance = field(default_factory=Provenance)
    raw_data: dict[str, Any] = field(default_factory=dict)  # Original data

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "facts": [f.to_dict() for f in self.facts],
            "inferences": [i.to_dict() for i in self.inferences],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "metrics": self.metrics,
            "confidence": self.confidence,
            "provenance": self.provenance.to_dict(),
            "raw_data": self.raw_data,
        }

    def get_truth_summary(self) -> dict:
        """Get summary of truthfulness layers."""
        return {
            "fact_count": len(self.facts),
            "inference_count": len(self.inferences),
            "recommendation_count": len(self.recommendations),
            "evidence_coverage": sum(len(f.evidence_refs) for f in self.facts),
        }

    def validate(self) -> list[str]:
        """Validate artifact structure."""
        issues = []

        # All facts must have evidence
        for i, f in enumerate(self.facts):
            if not f.evidence_refs:
                issues.append(f"Fact {i} has no evidence_refs")

        # Metrics must be 0-1
        for name, value in self.metrics.items():
            if not (0 <= value <= 1):
                issues.append(f"Metric '{name}' = {value} not in [0,1]")

        return issues


def create_artifact(
    kind: str,
    facts: list[dict] = None,
    inferences: list[dict] = None,
    recommendations: list[dict] = None,
    metrics: dict[str, float] = None,
    source_module: str = None,
) -> ArtifactBase:
    """Factory function to create artifacts."""
    artifact_facts = []
    if facts:
        for f in facts:
            refs = [EvidenceRef(**r) for r in f.get("evidence_refs", [])]
            if refs:
                artifact_facts.append(Fact(
                    statement=f["statement"],
                    evidence_refs=refs,
                    confidence=f.get("confidence", 1.0),
                ))

    artifact_inferences = []
    if inferences:
        for i in inferences:
            artifact_inferences.append(Inference(
                statement=i["statement"],
                method=i.get("method", "heuristic"),
                confidence=i.get("confidence", 0.5),
            ))

    artifact_recs = []
    if recommendations:
        for r in recommendations:
            artifact_recs.append(Recommendation(
                statement=r["statement"],
                rationale=r.get("rationale", ""),
                priority=r.get("priority", "medium"),
            ))

    provenance = Provenance(
        source_modules=[source_module] if source_module else [],
    )

    return ArtifactBase(
        kind=kind,
        facts=artifact_facts,
        inferences=artifact_inferences,
        recommendations=artifact_recs,
        metrics=metrics or {},
        provenance=provenance,
    )
