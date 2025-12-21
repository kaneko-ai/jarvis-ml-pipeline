"""Resolvers package for reference metadata enrichment.

Provides resolvers for:
- CrossRef (DOI lookup)
- PubMed (PMID lookup)
"""
from .crossref_resolver import resolve_crossref, CrossRefResult
from .pubmed_resolver import resolve_pubmed, PubMedResult

__all__ = [
    "resolve_crossref",
    "CrossRefResult",
    "resolve_pubmed",
    "PubMedResult",
]
