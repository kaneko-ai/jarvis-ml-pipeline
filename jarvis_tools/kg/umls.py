"""UMLS Integration.

Per RP-320, integrates UMLS for medical term standardization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class UMLSConcept:
    """A UMLS concept."""

    cui: str  # Concept Unique Identifier
    name: str
    semantic_types: List[str]
    synonyms: List[str]
    definition: Optional[str] = None


@dataclass
class NormalizedEntity:
    """An entity normalized to UMLS."""

    original: str
    cui: Optional[str]
    preferred_name: Optional[str]
    semantic_type: Optional[str]
    confidence: float
    alternatives: List[UMLSConcept]


class UMLSIntegration:
    """Integrates with UMLS Metathesaurus.

    Per RP-320:
    - UMLS Metathesaurus API integration
    - CUI-based entity normalization
    - Hierarchy retrieval
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_path: Optional[str] = None,
    ):
        self.api_key = api_key
        self.cache_path = cache_path
        self._cache: Dict[str, UMLSConcept] = {}
        self._load_local_cache()

    def _load_local_cache(self):
        """Load local cache of common terms."""
        # Common immunology terms
        local_concepts = {
            "cd73": UMLSConcept(
                cui="C0108788",
                name="5'-Nucleotidase",
                semantic_types=["Enzyme"],
                synonyms=["CD73", "NT5E", "ecto-5'-nucleotidase"],
            ),
            "cd39": UMLSConcept(
                cui="C0108462",
                name="CD39 Antigen",
                semantic_types=["Enzyme", "Immunologic Factor"],
                synonyms=["CD39", "ENTPD1", "NTPDase-1"],
            ),
            "adenosine": UMLSConcept(
                cui="C0001443",
                name="Adenosine",
                semantic_types=["Nucleoside"],
                synonyms=["adenosine", "9-beta-D-ribofuranosyladenine"],
            ),
            "pd-1": UMLSConcept(
                cui="C1418252",
                name="Programmed Cell Death 1",
                semantic_types=["Gene or Genome", "Immunologic Factor"],
                synonyms=["PD-1", "PDCD1", "CD279"],
            ),
            "ctla-4": UMLSConcept(
                cui="C0376611",
                name="CTLA-4 Antigen",
                semantic_types=["Amino Acid, Peptide, or Protein"],
                synonyms=["CTLA-4", "CD152", "Cytotoxic T-Lymphocyte Antigen 4"],
            ),
        }

        for key, concept in local_concepts.items():
            self._cache[key] = concept

    def normalize(self, term: str) -> NormalizedEntity:
        """Normalize a term to UMLS.

        Args:
            term: The term to normalize.

        Returns:
            NormalizedEntity with UMLS mapping.
        """
        term_lower = term.lower().strip()

        # Check cache
        if term_lower in self._cache:
            concept = self._cache[term_lower]
            return NormalizedEntity(
                original=term,
                cui=concept.cui,
                preferred_name=concept.name,
                semantic_type=concept.semantic_types[0] if concept.semantic_types else None,
                confidence=1.0,
                alternatives=[],
            )

        # Check synonyms
        for key, concept in self._cache.items():
            if term_lower in [s.lower() for s in concept.synonyms]:
                return NormalizedEntity(
                    original=term,
                    cui=concept.cui,
                    preferred_name=concept.name,
                    semantic_type=concept.semantic_types[0] if concept.semantic_types else None,
                    confidence=0.9,
                    alternatives=[],
                )

        # API lookup (placeholder)
        if self.api_key:
            return self._api_lookup(term)

        return NormalizedEntity(
            original=term,
            cui=None,
            preferred_name=None,
            semantic_type=None,
            confidence=0.0,
            alternatives=[],
        )

    def _api_lookup(self, term: str) -> NormalizedEntity:
        """Look up term via UMLS API."""
        # Placeholder for API integration
        return NormalizedEntity(
            original=term,
            cui=None,
            preferred_name=term,
            semantic_type=None,
            confidence=0.5,
            alternatives=[],
        )

    def get_hierarchy(self, cui: str) -> Dict[str, List[str]]:
        """Get concept hierarchy.

        Args:
            cui: UMLS CUI.

        Returns:
            Dict with 'parents', 'children', 'siblings'.
        """
        # Placeholder - would call UMLS API
        return {
            "parents": [],
            "children": [],
            "siblings": [],
        }

    def expand_with_synonyms(self, term: str) -> List[str]:
        """Expand term with UMLS synonyms.

        Args:
            term: The term to expand.

        Returns:
            List of synonyms including original.
        """
        norm = self.normalize(term)

        if norm.cui and norm.cui in [c.cui for c in self._cache.values()]:
            for concept in self._cache.values():
                if concept.cui == norm.cui:
                    return [term] + concept.synonyms

        return [term]
