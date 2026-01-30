"""Paper Multi-Attribute Vector System.

This module provides the foundational data structures for representing
papers as multi-dimensional knowledge points.

Per RP28, this is the FOUNDATION for all subsequent RPs (29-37).
All downstream features depend on this structure.

Design Principles:
1. No single giant vector - use semantic sub-vectors
2. Human-readable + machine-readable
3. Allow missing values (optional fields)
4. Version-aware for future schema evolution
5. Re-computable: can regenerate from source
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .reference import Reference
    from .result import EvidenceQAResult


# Schema version for compatibility tracking
VECTOR_SCHEMA_VERSION = "1.0.0"


@dataclass
class MetadataVector:
    """Objective/invariant metadata.

    Attributes:
        year: Publication year.
        journal: Journal name.
        publication_type: Type of publication.
        species: Species studied (human, mouse, etc).
        data_scale: Scale of data (single, bulk, single-cell, multi-omics).
    """

    year: int | None = None
    journal: str | None = None
    publication_type: Literal["original", "review", "preprint", "other"] = "other"
    species: list[str] = field(default_factory=list)
    data_scale: Literal["single", "bulk", "single-cell", "multi-omics", "unknown"] = "unknown"

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "journal": self.journal,
            "publication_type": self.publication_type,
            "species": self.species,
            "data_scale": self.data_scale,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MetadataVector:
        return cls(
            year=data.get("year"),
            journal=data.get("journal"),
            publication_type=data.get("publication_type", "other"),
            species=data.get("species", []),
            data_scale=data.get("data_scale", "unknown"),
        )


@dataclass
class ConceptVector:
    """Conceptual/thematic content.

    concepts: dict mapping normalized concept terms to importance scores (0-1).
    """

    concepts: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"concepts": self.concepts}

    @classmethod
    def from_dict(cls, data: dict) -> ConceptVector:
        return cls(concepts=data.get("concepts", {}))

    def top_concepts(self, k: int = 5) -> list[tuple[str, float]]:
        """Get top k concepts by score."""
        sorted_items = sorted(self.concepts.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:k]


@dataclass
class MethodVector:
    """Technical methods used.

    methods: dict mapping method names to presence/importance scores (0-1).
    """

    methods: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"methods": self.methods}

    @classmethod
    def from_dict(cls, data: dict) -> MethodVector:
        return cls(methods=data.get("methods", {}))


@dataclass
class BiologicalAxisVector:
    """Biological meaning space (interpretable axes).

    These are human-interpretable dimensions:
    - immune_activation: -1 (suppressive) to +1 (active)
    - metabolism_signal: -1 (metabolic) to +1 (signaling)
    - tumor_context: -1 (systemic) to +1 (TME/local)
    """

    immune_activation: float = 0.0
    metabolism_signal: float = 0.0
    tumor_context: float = 0.0

    def to_dict(self) -> dict:
        return {
            "immune_activation": self.immune_activation,
            "metabolism_signal": self.metabolism_signal,
            "tumor_context": self.tumor_context,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BiologicalAxisVector:
        return cls(
            immune_activation=data.get("immune_activation", 0.0),
            metabolism_signal=data.get("metabolism_signal", 0.0),
            tumor_context=data.get("tumor_context", 0.0),
        )

    def as_tuple(self) -> tuple[float, float, float]:
        """Get as 3D tuple for visualization."""
        return (self.immune_activation, self.metabolism_signal, self.tumor_context)


@dataclass
class TemporalVector:
    """Temporal context / research timeline position.

    novelty: 0 (derivative) to 1 (novel)
    paradigm_shift: degree of field transformation
    """

    novelty: float = 0.5
    paradigm_shift: float = 0.0

    def to_dict(self) -> dict:
        return {
            "novelty": self.novelty,
            "paradigm_shift": self.paradigm_shift,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TemporalVector:
        return cls(
            novelty=data.get("novelty", 0.5),
            paradigm_shift=data.get("paradigm_shift", 0.0),
        )


@dataclass
class ImpactVector:
    """Semantic impact assessment (ESTIMATED).

    All values are estimates and should be treated as such.
    citation_proxy: estimated citation impact
    downstream_density: density of follow-up research
    future_potential: estimated development potential
    """

    citation_proxy: float = 0.0
    downstream_density: float = 0.0
    future_potential: float = 0.5
    estimated: bool = True  # Always true - these are estimates

    def to_dict(self) -> dict:
        return {
            "citation_proxy": self.citation_proxy,
            "downstream_density": self.downstream_density,
            "future_potential": self.future_potential,
            "estimated": self.estimated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ImpactVector:
        return cls(
            citation_proxy=data.get("citation_proxy", 0.0),
            downstream_density=data.get("downstream_density", 0.0),
            future_potential=data.get("future_potential", 0.5),
            estimated=data.get("estimated", True),
        )


@dataclass
class EmbeddingVector:
    """Dense embedding vector (optional).

    Links to RP23 Vector Retriever for direct semantic comparison.
    """

    model: str = "dummy"
    vector: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "vector": self.vector,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EmbeddingVector:
        return cls(
            model=data.get("model", "dummy"),
            vector=data.get("vector", []),
        )


@dataclass
class PaperVector:
    """Complete multi-attribute vector for a paper.

    This is the central data structure that all downstream
    RPs (29-37) depend upon.

    Attributes:
        paper_id: Unique identifier.
        source_locator: Original source (pdf:... / url:...).
        metadata: Objective metadata.
        concept: Conceptual themes.
        method: Technical methods.
        biological_axis: Interpretable biological dimensions.
        temporal: Temporal/novelty context.
        impact: Estimated impact metrics.
        embedding: Optional dense embedding.
        generated_at: Timestamp of generation.
        version: Schema version for compatibility.
    """

    paper_id: str
    source_locator: str
    metadata: MetadataVector = field(default_factory=MetadataVector)
    concept: ConceptVector = field(default_factory=ConceptVector)
    method: MethodVector = field(default_factory=MethodVector)
    biological_axis: BiologicalAxisVector = field(default_factory=BiologicalAxisVector)
    temporal: TemporalVector = field(default_factory=TemporalVector)
    impact: ImpactVector = field(default_factory=ImpactVector)
    embedding: EmbeddingVector | None = None
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = VECTOR_SCHEMA_VERSION

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "paper_id": self.paper_id,
            "source_locator": self.source_locator,
            "metadata": self.metadata.to_dict(),
            "concept": self.concept.to_dict(),
            "method": self.method.to_dict(),
            "biological_axis": self.biological_axis.to_dict(),
            "temporal": self.temporal.to_dict(),
            "impact": self.impact.to_dict(),
            "embedding": self.embedding.to_dict() if self.embedding else None,
            "generated_at": self.generated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PaperVector:
        """Create from dictionary."""
        generated_at = data.get("generated_at")
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)
        elif generated_at is None:
            generated_at = datetime.now()

        embedding_data = data.get("embedding")
        embedding = EmbeddingVector.from_dict(embedding_data) if embedding_data else None

        return cls(
            paper_id=data["paper_id"],
            source_locator=data["source_locator"],
            metadata=MetadataVector.from_dict(data.get("metadata", {})),
            concept=ConceptVector.from_dict(data.get("concept", {})),
            method=MethodVector.from_dict(data.get("method", {})),
            biological_axis=BiologicalAxisVector.from_dict(data.get("biological_axis", {})),
            temporal=TemporalVector.from_dict(data.get("temporal", {})),
            impact=ImpactVector.from_dict(data.get("impact", {})),
            embedding=embedding,
            generated_at=generated_at,
            version=data.get("version", VECTOR_SCHEMA_VERSION),
        )

    def save(self, out_dir: str) -> str:
        """Save to JSON file.

        Args:
            out_dir: Base directory for paper_vectors.

        Returns:
            Path to saved file.
        """
        out_path = Path(out_dir)
        vectors_dir = out_path / "vectors"
        vectors_dir.mkdir(parents=True, exist_ok=True)

        file_path = vectors_dir / f"paper_{self.paper_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        # Update index
        _update_index(out_path, self.paper_id, self.source_locator)

        return str(file_path)

    @classmethod
    def load(cls, file_path: str) -> PaperVector:
        """Load from JSON file."""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


def _update_index(out_path: Path, paper_id: str, source_locator: str) -> None:
    """Update the index.json with new paper."""
    index_path = out_path / "index.json"

    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"papers": [], "version": VECTOR_SCHEMA_VERSION}

    # Add if not exists
    existing_ids = {p["paper_id"] for p in index["papers"]}
    if paper_id not in existing_ids:
        index["papers"].append(
            {
                "paper_id": paper_id,
                "source_locator": source_locator,
            }
        )

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def generate_paper_id(source_locator: str) -> str:
    """Generate a deterministic paper ID from source locator."""
    h = hashlib.sha256(source_locator.encode("utf-8")).hexdigest()
    return h[:12]


def extract_concepts_from_text(text: str) -> dict[str, float]:
    """Extract concept keywords from text (simplified).

    In production, this would use NLP/NER.
    """
    concepts = {}

    # Simple keyword detection
    keywords = [
        "CD73",
        "PD-1",
        "PD-L1",
        "CTLA-4",
        "Adenosine",
        "ATP",
        "T cell",
        "NK cell",
        "macrophage",
        "tumor",
        "cancer",
        "immunotherapy",
        "checkpoint",
        "inhibitor",
        "TME",
    ]

    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            # Count occurrences
            count = text_lower.count(kw.lower())
            # Normalize to 0-1 (cap at 10 occurrences)
            score = min(count / 10.0, 1.0)
            concepts[kw] = score

    return concepts


def extract_methods_from_text(text: str) -> dict[str, float]:
    """Extract method keywords from text (simplified)."""
    methods = {}

    method_keywords = [
        "scRNA-seq",
        "RNA-seq",
        "FACS",
        "flow cytometry",
        "Western blot",
        "qPCR",
        "ELISA",
        "mass spectrometry",
        "CRISPR",
        "knockout",
        "knockdown",
        "mouse model",
    ]

    text_lower = text.lower()
    for kw in method_keywords:
        if kw.lower() in text_lower:
            count = text_lower.count(kw.lower())
            score = min(count / 5.0, 1.0)
            methods[kw] = score

    return methods


def extract_paper_vector_from_result(
    result: EvidenceQAResult,
    reference: Reference | None = None,
) -> PaperVector:
    """Extract PaperVector from EvidenceQAResult.

    This is the main conversion function from Evidence Bundle
    to the multi-attribute vector representation.

    Args:
        result: The EvidenceQAResult.
        reference: Optional reference with metadata.

    Returns:
        PaperVector representing the paper.
    """
    # Gather all text for analysis
    all_text = result.answer
    if result.claims:
        for claim in result.claims.claims:
            all_text += " " + claim.text

    # Determine source locator
    source_locator = ""
    if result.inputs:
        source_locator = result.inputs[0]
    elif result.citations:
        source_locator = result.citations[0].locator

    paper_id = generate_paper_id(source_locator)

    # Build metadata
    metadata = MetadataVector()
    if reference:
        metadata.year = reference.year
        metadata.journal = reference.journal

    # Extract concepts and methods
    concepts = extract_concepts_from_text(all_text)
    methods = extract_methods_from_text(all_text)

    # Build biological axis (simplified heuristics)
    bio_axis = BiologicalAxisVector()
    text_lower = all_text.lower()

    # Immune activation axis
    if "suppression" in text_lower or "suppressive" in text_lower:
        bio_axis.immune_activation = -0.5
    if "activation" in text_lower or "stimulat" in text_lower:
        bio_axis.immune_activation = 0.5

    # Tumor context axis
    if "tme" in text_lower or "tumor microenvironment" in text_lower:
        bio_axis.tumor_context = 0.8
    if "systemic" in text_lower:
        bio_axis.tumor_context = -0.5

    return PaperVector(
        paper_id=paper_id,
        source_locator=source_locator,
        metadata=metadata,
        concept=ConceptVector(concepts=concepts),
        method=MethodVector(methods=methods),
        biological_axis=bio_axis,
    )


# ==================== Filter API ====================


def filter_by_year(
    vectors: list[PaperVector],
    min_year: int | None = None,
    max_year: int | None = None,
) -> list[PaperVector]:
    """Filter papers by publication year.

    Args:
        vectors: List of PaperVectors.
        min_year: Minimum year (inclusive).
        max_year: Maximum year (inclusive).

    Returns:
        Filtered list.
    """
    result = []
    for v in vectors:
        year = v.metadata.year
        if year is None:
            continue
        if min_year is not None and year < min_year:
            continue
        if max_year is not None and year > max_year:
            continue
        result.append(v)
    return result


def filter_by_concept(
    vectors: list[PaperVector],
    concept: str,
    min_score: float = 0.1,
) -> list[PaperVector]:
    """Filter papers by concept presence.

    Args:
        vectors: List of PaperVectors.
        concept: Concept to filter by.
        min_score: Minimum score threshold.

    Returns:
        Filtered list sorted by concept score.
    """
    result = []
    for v in vectors:
        score = v.concept.concepts.get(concept, 0.0)
        if score >= min_score:
            result.append((score, v))

    # Sort by score descending
    result.sort(key=lambda x: x[0], reverse=True)
    return [v for _, v in result]


def filter_by_year_and_concept(
    vectors: list[PaperVector],
    concept: str,
    min_year: int | None = None,
    max_year: int | None = None,
    min_score: float = 0.1,
) -> list[PaperVector]:
    """Filter by both year and concept.

    Args:
        vectors: List of PaperVectors.
        concept: Concept to filter by.
        min_year: Minimum year (inclusive).
        max_year: Maximum year (inclusive).
        min_score: Minimum concept score.

    Returns:
        Filtered and sorted list.
    """
    year_filtered = filter_by_year(vectors, min_year, max_year)
    return filter_by_concept(year_filtered, concept, min_score)


def load_all_vectors(vectors_dir: str) -> list[PaperVector]:
    """Load all paper vectors from a directory.

    Args:
        vectors_dir: Base directory containing paper_vectors.

    Returns:
        List of all PaperVectors.
    """
    vectors_path = Path(vectors_dir) / "vectors"
    if not vectors_path.exists():
        return []

    results = []
    for file_path in vectors_path.glob("paper_*.json"):
        try:
            pv = PaperVector.load(str(file_path))
            results.append(pv)
        except Exception as e:
            logger.debug(f"Failed to load paper vector from {file_path}: {e}")

    return results