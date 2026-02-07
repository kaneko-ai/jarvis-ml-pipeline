"""Mendeley API Client.

Integration with Mendeley reference manager.
Per JARVIS_COMPLETION_INSTRUCTION Task 3.1.2
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MendeleyConfig:
    """Mendeley API configuration."""

    access_token: str


class MendeleyClient:
    """Mendeley API client for reference management."""

    BASE_URL = "https://api.mendeley.com"

    def __init__(self, config: MendeleyConfig):
        """Initialize Mendeley client.

        Args:
            config: MendeleyConfig with access token
        """
        self._config = config
        self._headers = {
            "Authorization": f"Bearer {config.access_token}",
            "Accept": "application/vnd.mendeley-document.1+json",
        }

    def get_documents(
        self,
        folder_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get documents from Mendeley library.

        Args:
            folder_id: Optional folder to filter
            limit: Maximum documents to return

        Returns:
            List of Mendeley document dictionaries
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Mendeley integration")

        url = f"{self.BASE_URL}/documents"
        params = {"limit": limit}
        if folder_id:
            params["folder_id"] = folder_id

        response = requests.get(url, headers=self._headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def create_document(self, document: dict[str, Any]) -> dict[str, Any]:
        """Create a new document in Mendeley.

        Args:
            document: Document data dictionary

        Returns:
            Created document response
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Mendeley integration")

        url = f"{self.BASE_URL}/documents"
        response = requests.post(url, headers=self._headers, json=document, timeout=30)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, limit: int = 25) -> list[dict[str, Any]]:
        """Search Mendeley catalog.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching documents
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Mendeley integration")

        url = f"{self.BASE_URL}/search/catalog"
        params = {"query": query, "limit": limit}
        response = requests.get(url, headers=self._headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def document_to_paper(self, mendeley_doc: dict[str, Any]) -> dict[str, Any]:
        """Convert Mendeley document to JARVIS paper format.

        Args:
            mendeley_doc: Mendeley document dictionary

        Returns:
            JARVIS paper dictionary
        """
        authors = []
        for author in mendeley_doc.get("authors", []):
            name = f"{author.get('last_name', '')} {author.get('first_name', '')}".strip()
            if name:
                authors.append(name)

        return {
            "id": mendeley_doc.get("id"),
            "title": mendeley_doc.get("title", ""),
            "authors": authors,
            "abstract": mendeley_doc.get("abstract", ""),
            "doi": mendeley_doc.get("identifiers", {}).get("doi"),
            "year": mendeley_doc.get("year"),
            "journal": mendeley_doc.get("source", ""),
            "source": "mendeley",
        }

    def paper_to_document(self, paper: dict[str, Any]) -> dict[str, Any]:
        """Convert JARVIS paper to Mendeley document format.

        Args:
            paper: JARVIS paper dictionary

        Returns:
            Mendeley document data dictionary
        """
        authors = []
        for name in paper.get("authors", []):
            parts = name.split()
            if parts:
                authors.append(
                    {
                        "first_name": " ".join(parts[:-1]) if len(parts) > 1 else "",
                        "last_name": parts[-1],
                    }
                )

        return {
            "type": "journal",
            "title": paper.get("title", ""),
            "authors": authors,
            "abstract": paper.get("abstract", ""),
            "identifiers": {"doi": paper.get("doi")} if paper.get("doi") else {},
            "year": paper.get("year"),
            "source": paper.get("journal", ""),
        }
