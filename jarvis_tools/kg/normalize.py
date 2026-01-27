"""Entity Normalizer.

Per RP-129, normalizes gene/protein/drug names using offline dictionaries.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


# Built-in minimal dictionary for immunology
BUILTIN_SYNONYMS: Dict[str, List[str]] = {
    "PD-1": ["PDCD1", "CD279", "programmed cell death 1"],
    "PD-L1": ["CD274", "B7-H1", "programmed death-ligand 1"],
    "CTLA-4": ["CTLA4", "CD152"],
    "CD73": ["NT5E", "5'-nucleotidase", "ecto-5'-nucleotidase"],
    "CD39": ["ENTPD1", "NTPDase-1"],
    "TIM-3": ["HAVCR2", "TIM3", "T-cell immunoglobulin mucin-3"],
    "LAG-3": ["LAG3", "CD223"],
    "TIGIT": ["WUCAM", "VSIG9"],
    "IDO1": ["IDO", "indoleamine 2,3-dioxygenase"],
    "A2AR": ["ADORA2A", "adenosine A2A receptor"],
    "IFN-γ": ["IFNG", "interferon gamma", "IFN-gamma"],
    "TNF-α": ["TNF", "TNFA", "tumor necrosis factor alpha"],
    "IL-6": ["interleukin 6", "interleukin-6"],
    "IL-2": ["interleukin 2", "interleukin-2"],
    "TGF-β": ["TGFB", "TGFB1", "transforming growth factor beta"],
    "FOXP3": ["forkhead box P3"],
    "CD4": ["T helper"],
    "CD8": ["cytotoxic T", "CTL"],
    "Treg": ["regulatory T cell", "regulatory T cells", "CD4+CD25+FOXP3+"],
    "TME": ["tumor microenvironment"],
}


class EntityNormalizer:
    """Normalizes entity names to canonical forms."""

    def __init__(self, custom_dict: Optional[Dict[str, List[str]]] = None):
        self._canonical: Dict[str, str] = {}  # synonym -> canonical
        self._build_index(BUILTIN_SYNONYMS)
        if custom_dict:
            self._build_index(custom_dict)

    def _build_index(self, synonyms: Dict[str, List[str]]) -> None:
        """Build reverse index from synonyms to canonical."""
        for canonical, aliases in synonyms.items():
            canonical_upper = canonical.upper()
            self._canonical[canonical_upper] = canonical

            for alias in aliases:
                alias_upper = alias.upper()
                self._canonical[alias_upper] = canonical

    def normalize(self, entity: str) -> str:
        """Normalize an entity to its canonical form.

        Args:
            entity: Entity name to normalize.

        Returns:
            Canonical form if found, otherwise original.
        """
        if not entity:
            return entity

        # Try exact match
        entity_upper = entity.upper().strip()
        if entity_upper in self._canonical:
            return self._canonical[entity_upper]

        # Try without special characters
        cleaned = re.sub(r"[^\w]", "", entity_upper)
        if cleaned in self._canonical:
            return self._canonical[cleaned]

        return entity

    def get_canonical(self, entity: str) -> Optional[str]:
        """Get canonical form or None if not found."""
        result = self.normalize(entity)
        return result if result != entity else None

    def get_synonyms(self, canonical: str) -> List[str]:
        """Get all synonyms for a canonical entity."""
        canonical_upper = canonical.upper()

        # Check if this is a canonical form
        for can, aliases in BUILTIN_SYNONYMS.items():
            if can.upper() == canonical_upper:
                return [can] + aliases

        return [canonical]

    def expand_query(self, query: str) -> str:
        """Expand query with synonyms.

        Args:
            query: Original query.

        Returns:
            Expanded query with OR'd synonyms.
        """
        words = query.split()
        expansions = []

        for word in words:
            canonical = self.get_canonical(word)
            if canonical:
                synonyms = self.get_synonyms(canonical)[:3]
                if len(synonyms) > 1:
                    expansion = "(" + " OR ".join(synonyms) + ")"
                    expansions.append(expansion)
                else:
                    expansions.append(word)
            else:
                expansions.append(word)

        return " ".join(expansions)


# Global normalizer
_normalizer: Optional[EntityNormalizer] = None


def get_normalizer() -> EntityNormalizer:
    """Get global entity normalizer."""
    global _normalizer
    if _normalizer is None:
        _normalizer = EntityNormalizer()
    return _normalizer


def normalize_entity(entity: str) -> str:
    """Normalize an entity using the global normalizer."""
    return get_normalizer().normalize(entity)


def expand_query_with_synonyms(query: str) -> str:
    """Expand a query with synonyms."""
    return get_normalizer().expand_query(query)
