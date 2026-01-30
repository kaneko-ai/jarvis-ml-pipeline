"""Resolvers package for reference metadata enrichment.

Provides resolvers for:
- CrossRef (DOI lookup)
- PubMed (PMID lookup)
"""

from .crossref_resolver import CrossRefResult, resolve_crossref
from .pubmed_resolver import PubMedResult, resolve_pubmed

__all__ = [
    "resolve_crossref",
    "CrossRefResult",
    "resolve_pubmed",
    "PubMedResult",
]