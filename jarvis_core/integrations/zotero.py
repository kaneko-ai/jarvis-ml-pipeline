"""Zotero API Client.

Integration with Zotero reference manager.
Per JARVIS_COMPLETION_INSTRUCTION Task 3.1.1
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ZoteroConfig:
    """Zotero API configuration."""

    api_key: str
    user_id: str
    library_type: str = "user"  # "user" or "group"


class ZoteroClient:
    """Zotero API client for reference management."""

    BASE_URL = "https://api.zotero.org"

    def __init__(self, config: ZoteroConfig):
        """Initialize Zotero client.

        Args:
            config: ZoteroConfig with API credentials
        """
        self._config = config
        self._headers = {
            "Zotero-API-Key": config.api_key,
            "Zotero-API-Version": "3",
        }

    def _get_library_url(self) -> str:
        """Get the library URL based on type."""
        if self._config.library_type == "user":
            return f"{self.BASE_URL}/users/{self._config.user_id}"
        return f"{self.BASE_URL}/groups/{self._config.user_id}"

    def get_items(
        self,
        collection_key: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get items from Zotero library.

        Args:
            collection_key: Optional collection to filter
            limit: Maximum items to return

        Returns:
            List of Zotero item dictionaries
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Zotero integration")

        url = f"{self._get_library_url()}/items"
        params = {"limit": limit, "format": "json"}
        if collection_key:
            params["collection"] = collection_key

        response = requests.get(url, headers=self._headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def create_item(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new item in Zotero.

        Args:
            item_data: Item data dictionary

        Returns:
            Created item response
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Zotero integration")

        url = f"{self._get_library_url()}/items"
        response = requests.post(url, headers=self._headers, json=[item_data], timeout=30)
        response.raise_for_status()
        return response.json()

    def get_collections(self) -> list[dict[str, Any]]:
        """Get all collections in the library."""
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Zotero integration")

        url = f"{self._get_library_url()}/collections"
        response = requests.get(url, headers=self._headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, limit: int = 25) -> list[dict[str, Any]]:
        """Search items in library.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching items
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Zotero integration")

        url = f"{self._get_library_url()}/items"
        params = {"q": query, "limit": limit, "format": "json"}
        response = requests.get(url, headers=self._headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def item_to_paper(self, zotero_item: dict[str, Any]) -> dict[str, Any]:
        """Convert Zotero item to JARVIS paper format.

        Args:
            zotero_item: Zotero item dictionary

        Returns:
            JARVIS paper dictionary
        """
        data = zotero_item.get("data", {})
        return {
            "id": zotero_item.get("key"),
            "title": data.get("title", ""),
            "authors": [c.get("lastName", "") for c in data.get("creators", [])],
            "abstract": data.get("abstractNote", ""),
            "doi": data.get("DOI"),
            "year": data.get("date", "")[:4] if data.get("date") else None,
            "journal": data.get("publicationTitle", ""),
            "source": "zotero",
        }

    def paper_to_item(self, paper: dict[str, Any]) -> dict[str, Any]:
        """Convert JARVIS paper to Zotero item format.

        Args:
            paper: JARVIS paper dictionary

        Returns:
            Zotero item data dictionary
        """
        return {
            "itemType": "journalArticle",
            "title": paper.get("title", ""),
            "creators": [{"creatorType": "author", "name": a} for a in paper.get("authors", [])],
            "abstractNote": paper.get("abstract", ""),
            "DOI": paper.get("doi"),
            "date": str(paper.get("year", "")),
            "publicationTitle": paper.get("journal", ""),
        }
