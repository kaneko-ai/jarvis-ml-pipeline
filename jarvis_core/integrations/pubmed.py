"""PubMed API Client - Task 4: Real API Integration"""

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class PaperResult:
    """Research paper result."""

    pmid: str
    title: str
    authors: list[str]
    journal: str
    pub_date: str
    abstract: str
    doi: str | None = None

    def to_dict(self) -> dict:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "pub_date": self.pub_date,
            "abstract": self.abstract[:200] + "..." if len(self.abstract) > 200 else self.abstract,
            "doi": self.doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}",
        }


class PubMedClient:
    """Client for PubMed E-utilities API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: str | None = None):
        """Initialize PubMed client.

        Args:
            api_key: Optional NCBI API key for higher rate limits
        """
        self.api_key = api_key

    def search(self, query: str, max_results: int = 10) -> list[str]:
        """Search PubMed and return PMIDs.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of PMIDs
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/esearch.fcgi?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def fetch_details(self, pmids: list[str]) -> list[PaperResult]:
        """Fetch paper details for given PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of PaperResult objects
        """
        if not pmids:
            return []

        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json", "rettype": "abstract"}

        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/esummary.fcgi?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                results = []

                result_data = data.get("result", {})
                for pmid in pmids:
                    if pmid in result_data:
                        paper = result_data[pmid]
                        results.append(
                            PaperResult(
                                pmid=pmid,
                                title=paper.get("title", "Unknown"),
                                authors=[a.get("name", "") for a in paper.get("authors", [])[:5]],
                                journal=paper.get("source", "Unknown"),
                                pub_date=paper.get("pubdate", "Unknown"),
                                abstract=paper.get("abstract", "No abstract available"),
                                doi=paper.get("elocationid", None),
                            )
                        )

                return results
        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []

    def search_and_fetch(self, query: str, max_results: int = 10) -> list[dict]:
        """Search and fetch paper details in one call.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        pmids = self.search(query, max_results)
        papers = self.fetch_details(pmids)
        return [p.to_dict() for p in papers]


class MockPubMedClient:
    """Mock PubMed client for testing and development."""

    def search_and_fetch(self, query: str, max_results: int = 5) -> list[dict]:
        """Return mock search results.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of mock paper dictionaries
        """
        import random
        import time

        # Simulate network delay
        time.sleep(0.5)

        titles = [
            f"Novel approaches to {query}",
            f"Clinical review of {query}",
            f"Advances in {query} research",
            f"{query}: A comprehensive study",
            f"Machine learning applications in {query}",
            f"Recent developments in {query}",
            f"Systematic review of {query}",
            f"Meta-analysis of {query} treatments",
        ]

        authors = [
            ["Smith J", "Johnson A", "Williams B"],
            ["Brown C", "Davis D", "Miller E"],
            ["Wilson F", "Moore G", "Taylor H"],
            ["Anderson I", "Thomas J", "Jackson K"],
        ]

        journals = ["Nature Medicine", "JAMA", "Lancet", "NEJM", "Science", "Cell"]

        results = []
        for i in range(min(max_results, len(titles))):
            pmid = f"39{random.randint(100000, 999999)}"
            results.append(
                {
                    "pmid": pmid,
                    "title": titles[i],
                    "authors": random.choice(authors),
                    "journal": random.choice(journals),
                    "pub_date": f"2024 {random.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May'])}",
                    "abstract": f"This study investigates {query} and its implications...",
                    "doi": f"10.1000/jarvis.{pmid}",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                }
            )

        return results


def get_pubmed_client(use_mock: bool = False) -> PubMedClient:
    """Get PubMed client instance.

    Args:
        use_mock: If True, return mock client

    Returns:
        PubMed client instance
    """
    if use_mock:
        return MockPubMedClient()
    return PubMedClient()


# Global instance
_client = None


def search_papers(query: str, max_results: int = 10, use_mock: bool = True) -> list[dict]:
    """Search for papers using PubMed API.

    Args:
        query: Search query
        max_results: Maximum number of results
        use_mock: Use mock client (for development)

    Returns:
        List of paper dictionaries
    """
    global _client
    if _client is None:
        _client = get_pubmed_client(use_mock)

    return _client.search_and_fetch(query, max_results)


if __name__ == "__main__":
    # Demo
    print("Searching for 'COVID-19 treatment'...")
    results = search_papers("COVID-19 treatment", max_results=5, use_mock=True)

    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'])}")
        print(f"   Journal: {paper['journal']} ({paper['pub_date']})")
        print(f"   PMID: {paper['pmid']}")