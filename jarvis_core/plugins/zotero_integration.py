"""Zotero Integration Plugin for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 3.2: 外部連携
Provides integration with Zotero reference manager.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import requests

from .plugin_system import PluginType, SourcePlugin, register_plugin

logger = logging.getLogger(__name__)

ZOTERO_API_BASE = "https://api.zotero.org"


@dataclass
class ZoteroItem:
    """Zotero item representation."""

    key: str
    item_type: str
    title: str
    creators: list[str]
    date: str = ""
    doi: str | None = None
    abstract: str = ""
    tags: list[str] = None
    collections: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.collections is None:
            self.collections = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "item_type": self.item_type,
            "title": self.title,
            "creators": self.creators,
            "date": self.date,
            "doi": self.doi,
            "abstract": self.abstract,
            "tags": self.tags,
        }


class ZoteroClient:
    """Client for Zotero Web API.

    Supports both user and group libraries.
    """

    def __init__(
        self,
        api_key: str | None = None,
        user_id: str | None = None,
        group_id: str | None = None,
        library_id: str | None = None,
    ):
        self.api_key = api_key or os.getenv("ZOTERO_API_KEY")
        # `library_id` is accepted as a legacy alias for `user_id`.
        self.user_id = user_id or library_id or os.getenv("ZOTERO_USER_ID")
        self.group_id = group_id or os.getenv("ZOTERO_GROUP_ID")

        self._session = requests.Session()
        if self.api_key:
            self._session.headers["Zotero-API-Key"] = self.api_key
        self._session.headers["Zotero-API-Version"] = "3"

    @property
    def library_url(self) -> str:
        """Get the library URL prefix."""
        if self.group_id:
            return f"{ZOTERO_API_BASE}/groups/{self.group_id}"
        elif self.user_id:
            return f"{ZOTERO_API_BASE}/users/{self.user_id}"
        raise ValueError("Either user_id or group_id must be set")

    def is_available(self) -> bool:
        """Check if Zotero API is accessible."""
        if not self.api_key or not (self.user_id or self.group_id):
            return False

        try:
            response = self._session.get(
                f"{self.library_url}/items/top",
                params={"limit": 1},
                timeout=10,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_items(
        self,
        limit: int = 25,
        start: int = 0,
        item_type: str | None = None,
        tag: str | None = None,
        collection: str | None = None,
    ) -> list[ZoteroItem]:
        """Get items from library.

        Args:
            limit: Maximum items to return.
            start: Offset for pagination.
            item_type: Filter by item type.
            tag: Filter by tag.
            collection: Filter by collection key.

        Returns:
            List of ZoteroItem objects.
        """
        url = f"{self.library_url}/items"
        if collection:
            url = f"{self.library_url}/collections/{collection}/items"

        params = {
            "limit": min(limit, 100),
            "start": start,
            "format": "json",
        }

        if item_type:
            params["itemType"] = item_type
        if tag:
            params["tag"] = tag

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()

            items = []
            for data in response.json():
                item = self._parse_item(data)
                if item:
                    items.append(item)

            return items

        except requests.RequestException as e:
            logger.error(f"Zotero get items error: {e}")
            return []

    def search(
        self,
        query: str,
        limit: int = 25,
    ) -> list[ZoteroItem]:
        """Search items in library.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of matching items.
        """
        url = f"{self.library_url}/items"
        params = {
            "q": query,
            "limit": min(limit, 100),
            "format": "json",
        }

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()

            items = []
            for data in response.json():
                item = self._parse_item(data)
                if item:
                    items.append(item)

            return items

        except requests.RequestException as e:
            logger.error(f"Zotero search error: {e}")
            return []

    def get_item(self, item_key: str) -> ZoteroItem | None:
        """Get a specific item by key."""
        url = f"{self.library_url}/items/{item_key}"

        try:
            response = self._session.get(url, timeout=30)
            response.raise_for_status()
            return self._parse_item(response.json())

        except requests.RequestException as e:
            logger.error(f"Zotero get item error: {e}")
            return None

    def get_collections(self) -> list[dict[str, Any]]:
        """Get all collections."""
        url = f"{self.library_url}/collections"

        try:
            response = self._session.get(url, timeout=30)
            response.raise_for_status()

            collections = []
            for data in response.json():
                collections.append(
                    {
                        "key": data.get("key"),
                        "name": data.get("data", {}).get("name", ""),
                        "parent": data.get("data", {}).get("parentCollection"),
                    }
                )

            return collections

        except requests.RequestException as e:
            logger.error(f"Zotero get collections error: {e}")
            return []

    def _parse_item(self, data: dict) -> ZoteroItem | None:
        """Parse Zotero API response into ZoteroItem."""
        try:
            item_data = data.get("data", {})

            # Extract creators
            creators = []
            for creator in item_data.get("creators", []):
                if creator.get("name"):
                    creators.append(creator["name"])
                elif creator.get("lastName"):
                    name = creator["lastName"]
                    if creator.get("firstName"):
                        name = f"{name}, {creator['firstName']}"
                    creators.append(name)

            # Extract tags
            tags = [t.get("tag", "") for t in item_data.get("tags", [])]

            return ZoteroItem(
                key=data.get("key", ""),
                item_type=item_data.get("itemType", ""),
                title=item_data.get("title", ""),
                creators=creators,
                date=item_data.get("date", ""),
                doi=item_data.get("DOI"),
                abstract=item_data.get("abstractNote", ""),
                tags=tags,
                collections=item_data.get("collections", []),
            )

        except Exception as e:
            logger.error(f"Failed to parse Zotero item: {e}")
            return None


@register_plugin
class ZoteroPlugin(SourcePlugin):
    """Zotero integration plugin."""

    NAME = "zotero"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.INTEGRATION
    DESCRIPTION = "Integration with Zotero reference manager"
    AUTHOR = "JARVIS Team"

    def __init__(self):
        super().__init__()
        self.client: ZoteroClient | None = None

    def initialize(self) -> bool:
        """Initialize Zotero client."""
        try:
            self.client = ZoteroClient()
            return True
        except Exception as e:
            logger.error(f"Zotero plugin init error: {e}")
            return False

    def search(self, query: str, **kwargs) -> list[dict]:
        """Search Zotero library."""
        if not self.client:
            return []

        items = self.client.search(query, limit=kwargs.get("limit", 25))
        return [item.to_dict() for item in items]

    def fetch(self, item_id: str, **kwargs) -> dict | None:
        """Fetch a Zotero item."""
        if not self.client:
            return None

        item = self.client.get_item(item_id)
        return item.to_dict() if item else None

    def get_collections(self) -> list[dict]:
        """Get Zotero collections."""
        if not self.client:
            return []
        return self.client.get_collections()
