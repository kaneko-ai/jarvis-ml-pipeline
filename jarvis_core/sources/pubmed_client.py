"""NCBI PubMed Client for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.4: 無料API統合
Uses NCBI E-utilities API (free, no API key required for low volume).
"""
from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# NCBI E-utilities base URLs
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"
EINFO_URL = f"{EUTILS_BASE}/einfo.fcgi"


@dataclass
class PubMedArticle:
    """PubMed article representation."""
    pmid: str
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    pub_date: str = ""
    doi: Optional[str] = None
    pmc_id: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    mesh_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "journal": self.journal,
            "pub_date": self.pub_date,
            "doi": self.doi,
            "pmc_id": self.pmc_id,
            "keywords": self.keywords,
            "mesh_terms": self.mesh_terms,
        }


class PubMedClient:
    """Client for NCBI PubMed E-utilities API.
    
    Free API with rate limiting (3 requests/second without API key).
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        email: Optional[str] = None,
        tool_name: str = "jarvis-research-os",
        rate_limit: float = 0.34,  # ~3 requests/second
    ):
        self.api_key = api_key
        self.email = email
        self.tool_name = tool_name
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._session = requests.Session()
    
    def _rate_limit_wait(self) -> None:
        """Wait for rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()
    
    def _build_params(self, **kwargs) -> Dict[str, str]:
        """Build request parameters with common fields."""
        params = {
            "tool": self.tool_name,
            **kwargs,
        }
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params
    
    def search(
        self,
        query: str,
        max_results: int = 20,
        sort: str = "relevance",
    ) -> List[str]:
        """Search PubMed and return PMIDs.
        
        Args:
            query: Search query (PubMed query syntax).
            max_results: Maximum number of results.
            sort: Sort order ('relevance' or 'date').
            
        Returns:
            List of PMIDs.
        """
        self._rate_limit_wait()
        
        params = self._build_params(
            db="pubmed",
            term=query,
            retmax=str(max_results),
            sort=sort,
            retmode="json",
        )
        
        try:
            response = self._session.get(ESEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            id_list = data.get("esearchresult", {}).get("idlist", [])
            logger.info(f"PubMed search '{query[:50]}...' returned {len(id_list)} results")
            return id_list
            
        except requests.RequestException as e:
            logger.error(f"PubMed search error: {e}")
            return []
    
    def fetch(self, pmids: List[str]) -> List[PubMedArticle]:
        """Fetch article details by PMIDs.
        
        Args:
            pmids: List of PubMed IDs.
            
        Returns:
            List of PubMedArticle objects.
        """
        if not pmids:
            return []
        
        self._rate_limit_wait()
        
        params = self._build_params(
            db="pubmed",
            id=",".join(pmids),
            retmode="xml",
        )
        
        try:
            response = self._session.get(EFETCH_URL, params=params, timeout=60)
            response.raise_for_status()
            
            articles = self._parse_pubmed_xml(response.text)
            logger.info(f"Fetched {len(articles)} articles from PubMed")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"PubMed fetch error: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_text: str) -> List[PubMedArticle]:
        """Parse PubMed XML response."""
        articles = []
        
        try:
            root = ET.fromstring(xml_text)
            
            for article_elem in root.findall(".//PubmedArticle"):
                articles.append(self._parse_article(article_elem))
                
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
        
        return articles
    
    def _parse_article(self, elem: ET.Element) -> PubMedArticle:
        """Parse single article element."""
        medline = elem.find("MedlineCitation")
        article = medline.find("Article") if medline is not None else None
        
        # PMID
        pmid_elem = medline.find("PMID") if medline else None
        pmid = pmid_elem.text if pmid_elem is not None else ""
        
        # Title
        title_elem = article.find("ArticleTitle") if article else None
        title = title_elem.text if title_elem is not None else ""
        
        # Abstract
        abstract_parts = []
        if article:
            abstract_elem = article.find("Abstract")
            if abstract_elem:
                for text in abstract_elem.findall("AbstractText"):
                    label = text.get("Label", "")
                    content = text.text or ""
                    if label:
                        abstract_parts.append(f"{label}: {content}")
                    else:
                        abstract_parts.append(content)
        abstract = " ".join(abstract_parts)
        
        # Authors
        authors = []
        if article:
            author_list = article.find("AuthorList")
            if author_list:
                for author in author_list.findall("Author"):
                    last = author.find("LastName")
                    first = author.find("ForeName")
                    if last is not None:
                        name = last.text or ""
                        if first is not None and first.text:
                            name = f"{name} {first.text}"
                        authors.append(name)
        
        # Journal
        journal = ""
        if article:
            journal_elem = article.find("Journal/Title")
            if journal_elem is not None:
                journal = journal_elem.text or ""
        
        # Date
        pub_date = ""
        if article:
            date_elem = article.find("Journal/JournalIssue/PubDate")
            if date_elem:
                year = date_elem.find("Year")
                month = date_elem.find("Month")
                if year is not None:
                    pub_date = year.text or ""
                    if month is not None and month.text:
                        pub_date = f"{pub_date}-{month.text}"
        
        # DOI
        doi = None
        if article:
            for id_elem in article.findall("ELocationID"):
                if id_elem.get("EIdType") == "doi":
                    doi = id_elem.text
                    break
        
        # MeSH terms
        mesh_terms = []
        if medline:
            mesh_list = medline.find("MeshHeadingList")
            if mesh_list:
                for mesh in mesh_list.findall("MeshHeading/DescriptorName"):
                    if mesh.text:
                        mesh_terms.append(mesh.text)
        
        return PubMedArticle(
            pmid=pmid,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            pub_date=pub_date,
            doi=doi,
            mesh_terms=mesh_terms,
        )
    
    def search_and_fetch(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[PubMedArticle]:
        """Search and fetch articles in one call.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            
        Returns:
            List of PubMedArticle objects.
        """
        pmids = self.search(query, max_results=max_results)
        if not pmids:
            return []
        return self.fetch(pmids)
