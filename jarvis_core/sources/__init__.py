"""Sources package - Free API clients for academic literature.

Provides clients for:
- NCBI PubMed (E-utilities)
- Semantic Scholar
- OpenAlex
- arXiv (C-5)
- Crossref (C-5)
- Unpaywall
"""

from .chunking import (
    Chunker,
    ChunkResult,
    ExecutionContext,
    SourceDocument,
    ingest,
)
from .arxiv_client import ArxivClient, ArxivPaper
from .crossref_client import CrossrefClient, CrossrefWork
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
    "ArxivClient",
    "ArxivPaper",
    "CrossrefClient",
    "CrossrefWork",
    "UnifiedSourceClient",
    "SourceDocument",
    "Chunker",
    "ingest",
    "ChunkResult",
    "ExecutionContext",
]
