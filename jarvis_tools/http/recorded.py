"""Recorded HTTP Client.

Per PR-63, provides network-isolated testing via recorded fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class RecordedResponse:
    """A recorded HTTP response."""

    status_code: int
    headers: Dict[str, str]
    body: str
    url: str

    def json(self) -> Any:
        return json.loads(self.body)

    @property
    def text(self) -> str:
        return self.body


class RecordedHTTPClient:
    """HTTP client that uses recorded fixtures instead of real network.

    Usage:
        client = RecordedHTTPClient("tests/fixtures/http")
        response = client.get("pubmed_esearch", {"term": "CD73"})
    """

    def __init__(self, fixtures_dir: str = "tests/fixtures/http"):
        self.fixtures_dir = Path(fixtures_dir)
        self._cache: Dict[str, RecordedResponse] = {}

    def _load_fixture(self, fixture_name: str) -> Optional[RecordedResponse]:
        """Load a fixture by name."""
        fixture_path = self.fixtures_dir / f"{fixture_name}.json"

        if not fixture_path.exists():
            return None

        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return RecordedResponse(
            status_code=data.get("status_code", 200),
            headers=data.get("headers", {}),
            body=data.get("body", ""),
            url=data.get("url", ""),
        )

    def get(self, fixture_name: str, params: Optional[Dict] = None) -> RecordedResponse:
        """Get a recorded response."""
        if fixture_name in self._cache:
            return self._cache[fixture_name]

        response = self._load_fixture(fixture_name)
        if response is None:
            raise FileNotFoundError(
                f"No recorded fixture for '{fixture_name}'. "
                f"Expected at: {self.fixtures_dir / f'{fixture_name}.json'}"
            )

        self._cache[fixture_name] = response
        return response

    def has_fixture(self, fixture_name: str) -> bool:
        """Check if a fixture exists."""
        return (self.fixtures_dir / f"{fixture_name}.json").exists()


# Global recorded mode flag
_RECORDED_MODE = False


def set_recorded_mode(enabled: bool) -> None:
    """Enable/disable recorded HTTP mode."""
    global _RECORDED_MODE
    _RECORDED_MODE = enabled


def is_recorded_mode() -> bool:
    """Check if recorded mode is enabled."""
    return _RECORDED_MODE


# Singleton client
_client: Optional[RecordedHTTPClient] = None


def get_recorded_client(fixtures_dir: str = "tests/fixtures/http") -> RecordedHTTPClient:
    """Get the global recorded HTTP client."""
    global _client
    if _client is None:
        _client = RecordedHTTPClient(fixtures_dir)
    return _client
