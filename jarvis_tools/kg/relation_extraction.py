"""Relation Extraction v2.

Per RP-322, extracts relations with high precision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class RelationType(Enum):
    """Biomedical relation types."""

    TREATS = "treats"
    CAUSES = "causes"
    INHIBITS = "inhibits"
    ACTIVATES = "activates"
    ASSOCIATED_WITH = "associated_with"
    REGULATES = "regulates"
    BINDS = "binds"
    EXPRESSES = "expresses"
    METABOLIZES = "metabolizes"
    PREVENTS = "prevents"


@dataclass
class ExtractedRelation:
    """An extracted relation."""

    subject: str
    subject_type: str
    relation: RelationType
    object: str
    object_type: str
    confidence: float
    evidence: str
    source_span: Tuple[int, int]


# Relation patterns
RELATION_PATTERNS = {
    RelationType.TREATS: [
        r"(\w+(?:\s+\w+)?)\s+(?:treats?|is\s+used\s+to\s+treat|therapy\s+for)\s+(\w+(?:\s+\w+)?)",
        r"treatment\s+of\s+(\w+)\s+with\s+(\w+)",
    ],
    RelationType.CAUSES: [
        r"(\w+)\s+(?:causes?|leads?\s+to|results?\s+in)\s+(\w+)",
        r"(\w+)\s+(?:induced?|triggers?)\s+(\w+)",
    ],
    RelationType.INHIBITS: [
        r"(\w+)\s+(?:inhibits?|blocks?|suppresses?)\s+(\w+)",
        r"inhibition\s+of\s+(\w+)\s+by\s+(\w+)",
    ],
    RelationType.ACTIVATES: [
        r"(\w+)\s+(?:activates?|stimulates?|promotes?)\s+(\w+)",
        r"activation\s+of\s+(\w+)\s+by\s+(\w+)",
    ],
    RelationType.REGULATES: [
        r"(\w+)\s+(?:regulates?|modulates?|controls?)\s+(\w+)",
        r"regulation\s+of\s+(\w+)\s+by\s+(\w+)",
    ],
    RelationType.BINDS: [
        r"(\w+)\s+(?:binds?\s+to|interacts?\s+with)\s+(\w+)",
        r"binding\s+of\s+(\w+)\s+to\s+(\w+)",
    ],
}


class RelationExtractor:
    """Extracts biomedical relations.

    Per RP-322:
    - High precision relation extraction
    - Confidence scoring
    - Multiple relation types
    """

    def __init__(
        self,
        model=None,
        min_confidence: float = 0.5,
    ):
        self.model = model
        self.min_confidence = min_confidence

    def extract(
        self,
        text: str,
        entities: Optional[List[Dict]] = None,
    ) -> List[ExtractedRelation]:
        """Extract relations from text.

        Args:
            text: Input text.
            entities: Optional pre-extracted entities.

        Returns:
            List of extracted relations.
        """
        relations = []

        # Pattern-based extraction
        for rel_type, patterns in RELATION_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    subj = match.group(1).strip()
                    obj = match.group(2).strip()

                    # Validate entities
                    if len(subj) < 2 or len(obj) < 2:
                        continue

                    # Calculate confidence
                    confidence = self._calculate_confidence(match, text)

                    if confidence >= self.min_confidence:
                        relations.append(
                            ExtractedRelation(
                                subject=subj,
                                subject_type=self._infer_type(subj),
                                relation=rel_type,
                                object=obj,
                                object_type=self._infer_type(obj),
                                confidence=confidence,
                                evidence=match.group(0),
                                source_span=(match.start(), match.end()),
                            )
                        )

        # Model-based extraction (if available)
        if self.model:
            model_relations = self._model_extract(text)
            relations.extend(model_relations)

        # Deduplicate
        relations = self._deduplicate(relations)

        return relations

    def _calculate_confidence(
        self,
        match,
        text: str,
    ) -> float:
        """Calculate extraction confidence."""
        confidence = 0.7

        # Boost for exact verb matches
        matched_text = match.group(0).lower()
        exact_verbs = ["inhibits", "activates", "treats", "causes"]
        if any(v in matched_text for v in exact_verbs):
            confidence += 0.1

        # Boost for sentence boundary
        start = match.start()
        if start == 0 or text[start - 1] in ".!?":
            confidence += 0.1

        return min(confidence, 1.0)

    def _infer_type(self, entity: str) -> str:
        """Infer entity type."""
        entity_lower = entity.lower()

        # Gene/protein patterns
        if re.match(r"^[A-Z][A-Z0-9]{1,5}$", entity):
            return "gene"

        # Drug patterns
        if entity_lower.endswith(("inib", "mab", "zumab", "ine")):
            return "drug"

        # Disease patterns
        if any(kw in entity_lower for kw in ["cancer", "disease", "syndrome", "oma"]):
            return "disease"

        return "entity"

    def _model_extract(
        self,
        text: str,
    ) -> List[ExtractedRelation]:
        """Extract using ML model."""
        # Placeholder - would use PubMedBERT or similar
        return []

    def _deduplicate(
        self,
        relations: List[ExtractedRelation],
    ) -> List[ExtractedRelation]:
        """Remove duplicate relations."""
        seen = set()
        unique = []

        for rel in relations:
            key = (rel.subject.lower(), rel.relation, rel.object.lower())
            if key not in seen:
                seen.add(key)
                unique.append(rel)

        return unique

    def to_triples(
        self,
        relations: List[ExtractedRelation],
    ) -> List[Tuple[str, str, str]]:
        """Convert to simple triples.

        Args:
            relations: Extracted relations.

        Returns:
            List of (subject, predicate, object) tuples.
        """
        return [(r.subject, r.relation.value, r.object) for r in relations]
