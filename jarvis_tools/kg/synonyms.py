"""Synonym Expansion.

Per RP-25, provides offline synonym normalization for query expansion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Set

# Load synonyms from JSON
_SYNONYM_FILE = Path(__file__).parent / "synonyms" / "immuno_synonyms.json"
_SYNONYMS: dict[str, list[str]] = {}


def _load_synonyms() -> dict[str, list[str]]:
    """Load synonym dictionary."""
    global _SYNONYMS
    if not _SYNONYMS and _SYNONYM_FILE.exists():
        with open(_SYNONYM_FILE, "r", encoding="utf-8") as f:
            _SYNONYMS = json.load(f)
    return _SYNONYMS


def get_synonyms(term: str) -> List[str]:
    """Get synonyms for a term."""
    synonyms = _load_synonyms()

    # Direct lookup
    if term.upper() in synonyms:
        return synonyms[term.upper()]

    # Reverse lookup
    for canonical, aliases in synonyms.items():
        if term.upper() == canonical.upper() or term.lower() in [a.lower() for a in aliases]:
            return [canonical] + aliases

    return []


def expand_query(query: str, max_expansions: int = 5) -> str:
    """Expand query with synonyms.

    Args:
        query: Original query.
        max_expansions: Maximum synonyms to add.

    Returns:
        Expanded query.
    """
    synonyms = _load_synonyms()
    words = query.split()
    expanded_terms: Set[str] = set()

    for word in words:
        # Check if word matches a canonical term
        word_upper = word.upper().strip(".,;:")

        if word_upper in synonyms:
            # Add first N synonyms
            for syn in synonyms[word_upper][:max_expansions]:
                expanded_terms.add(syn)

        # Check reverse (if word is a synonym)
        for canonical, aliases in synonyms.items():
            if word.lower() in [a.lower() for a in aliases]:
                expanded_terms.add(canonical)
                break

    # Combine original query with expansions
    if expanded_terms:
        expansion = " OR ".join(expanded_terms)
        return f"({query}) OR ({expansion})"

    return query


def normalize_entity(entity: str) -> str:
    """Normalize entity to canonical form."""
    synonyms = _load_synonyms()
    entity_upper = entity.upper().strip()

    # Already canonical
    if entity_upper in synonyms:
        return entity_upper

    # Find canonical form
    for canonical, aliases in synonyms.items():
        if entity.lower() in [a.lower() for a in aliases]:
            return canonical

    return entity  # Return as-is if not found
