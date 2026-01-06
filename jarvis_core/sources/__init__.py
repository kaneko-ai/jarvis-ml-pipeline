"""Sources package - Free API clients for academic literature.

Provides clients for:
- NCBI PubMed (E-utilities)
- Semantic Scholar
- OpenAlex
- arXiv
- Crossref
- Unpaywall
"""

from .pubmed_client import PubMedClient, PubMedArticle
from .semantic_scholar_client import SemanticScholarClient, S2Paper
from .openalex_client import OpenAlexClient, OpenAlexWork
from .unified_source_client import UnifiedSourceClient

__all__ = [
    "PubMedClient",
    "PubMedArticle",
    "SemanticScholarClient",
    "S2Paper",
    "OpenAlexClient",
    "OpenAlexWork",
    "UnifiedSourceClient",
]
