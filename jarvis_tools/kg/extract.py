"""Triple Extraction.

Per RP-11, extracts triples from chunks using schema-guided extraction.
"""

from __future__ import annotations

import re
from typing import List, Optional, Any

from .store import Triple


# Simple biomedical relation patterns
RELATION_PATTERNS = [
    (r"(\w+)\s+(?:inhibits?|blocks?)\s+(\w+)", "inhibits"),
    (r"(\w+)\s+(?:activates?|induces?)\s+(\w+)", "activates"),
    (r"(\w+)\s+(?:expresses?|produces?)\s+(\w+)", "expresses"),
    (r"(\w+)\s+(?:binds?\s+to)\s+(\w+)", "binds_to"),
    (r"(\w+)\s+(?:regulates?)\s+(\w+)", "regulates"),
    (r"(\w+)\s+(?:is\s+associated\s+with)\s+(\w+)", "associated_with"),
]


def extract_triples_regex(
    text: str,
    pmid: Optional[str] = None,
    chunk_id: Optional[str] = None,
) -> List[Triple]:
    """Extract triples using regex patterns.

    Args:
        text: Text to extract from.
        pmid: Paper ID.
        chunk_id: Chunk ID.

    Returns:
        List of extracted triples.
    """
    triples = []

    for pattern, relation in RELATION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            triples.append(
                Triple(
                    entity1=match.group(1).upper(),
                    relation=relation,
                    entity2=match.group(2).upper(),
                    pmid=pmid,
                    chunk_id=chunk_id,
                )
            )

    return triples


def extract_triples(
    text: str,
    pmid: Optional[str] = None,
    chunk_id: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> List[Triple]:
    """Extract triples from text.

    Uses regex by default; if llm_client is provided, uses LLM extraction.

    Args:
        text: Text to extract from.
        pmid: Paper ID.
        chunk_id: Chunk ID.
        llm_client: Optional LLM client.

    Returns:
        List of triples.
    """
    # Always try regex first
    triples = extract_triples_regex(text, pmid, chunk_id)

    # LLM extraction is optional and additive
    if llm_client and len(triples) == 0:
        # Placeholder for LLM-based extraction
        # Would call llm_client.generate with schema prompt
        pass

    return triples
