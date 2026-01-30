"""Sources package - Free API clients for academic literature.

Provides clients for:
- NCBI PubMed (E-utilities)
- Semantic Scholar
- OpenAlex
- arXiv
- Crossref
- Unpaywall
"""

from .chunking import (
    Chunker,
    ChunkResult,
    ExecutionContext,
    SourceDocument,
    ingest,
)
from .openalex_client import OpenAlexClient, OpenAlexWork
from .pubmed_client import PubMedArticle, PubMedClient
from .semantic_scholar_client import S2Paper, SemanticScholarClient
from .unified_source_client import UnifiedSourceClient

__all__ = [
    "PubMedClient",
    "PubMedArticle",
    "SemanticScholarClient",
    "S2Paper",
    "OpenAlexClient",
    "OpenAlexWork",
    "UnifiedSourceClient",
    "SourceDocument",
    "Chunker",
    "ingest",
    "ChunkResult",
    "ExecutionContext",
]