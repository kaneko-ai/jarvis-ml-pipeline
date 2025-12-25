"""
JARVIS Connectors - PubMed/PMC リアルAPI

PubMed E-utilities経由で検索→PMID取得。
PMC優先でフルテキスト取得。
"""

from jarvis_core.connectors.pubmed import (
    PubMedConnector,
    search_pubmed,
    fetch_paper_details,
)
from jarvis_core.connectors.pmc import (
    PMCConnector,
    resolve_pmcid,
    fetch_fulltext,
)

__all__ = [
    "PubMedConnector",
    "search_pubmed",
    "fetch_paper_details",
    "PMCConnector",
    "resolve_pmcid",
    "fetch_fulltext",
]
