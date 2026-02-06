"""Unpaywall API Client.

Free API client for finding open access versions of papers.
Per JARVIS_COMPLETION_PLAN_v3 Task 1.4.5
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import requests

logger = logging.getLogger(__name__)

UNPAYWALL_BASE_URL = "https://api.unpaywall.org/v2"


@dataclass
class OALocation:
    """Open Access location information."""

    url: str
    is_pdf: bool = False
    version: str | None = None  # "publishedVersion", "acceptedVersion", etc.
    host_type: str | None = None  # "publisher", "repository"
    license: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "is_pdf": self.is_pdf,
            "version": self.version,
            "host_type": self.host_type,
            "license": self.license,
        }


@dataclass
class UnpaywallResult:
    """Result from Unpaywall API."""

    doi: str
    is_oa: bool
    title: str | None = None
    best_oa_location: OALocation | None = None
    oa_locations: list[OALocation] = field(default_factory=list)
    oa_status: str | None = None  # "gold", "green", "hybrid", "bronze", "closed"
    publisher: str | None = None
    journal: str | None = None

    def get_pdf_url(self) -> str | None:
        """Get the best PDF URL if available."""
        # First try best_oa_location
        if self.best_oa_location and self.best_oa_location.is_pdf:
            return self.best_oa_location.url

        # Look through all locations for a PDF
        for loc in self.oa_locations:
            if loc.is_pdf:
                return loc.url

        # Return any URL if no direct PDF found
        if self.best_oa_location:
            return self.best_oa_location.url
        if self.oa_locations:
            return self.oa_locations[0].url

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doi": self.doi,
            "is_oa": self.is_oa,
            "title": self.title,
            "best_oa_location": self.best_oa_location.to_dict() if self.best_oa_location else None,
            "oa_locations": [loc.to_dict() for loc in self.oa_locations],
            "oa_status": self.oa_status,
            "publisher": self.publisher,
            "journal": self.journal,
        }


class UnpaywallClient:
    """Client for the Unpaywall API.

    Finds open access versions of papers by DOI.

    Example:
        >>> client = UnpaywallClient(email="your@email.com")
        >>> result = client.get_oa_status("10.1038/nature12373")
        >>> if result.is_oa:
        ...     print(f"PDF available: {result.get_pdf_url()}")
    """

    def __init__(
        self,
        email: str,
        timeout: float = 30.0,
    ):
        """Initialize the Unpaywall client.

        Args:
            email: Email address (required by Unpaywall API)
            timeout: Request timeout in seconds
        """
        self._email = email
        self._timeout = timeout

    def get_oa_status(self, doi: str) -> UnpaywallResult | None:
        """Get open access status for a DOI.

        Args:
            doi: DOI to look up

        Returns:
            UnpaywallResult or None if not found
        """
        # Clean the DOI
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        doi = doi.strip()

        url = f"{UNPAYWALL_BASE_URL}/{doi}"
        params = {"email": self._email}

        try:
            response = requests.get(url, params=params, timeout=self._timeout)

            if response.status_code == 404:
                logger.debug(f"DOI not found in Unpaywall: {doi}")
                return UnpaywallResult(
                    doi=doi,
                    is_oa=False,
                )

            response.raise_for_status()
            data = response.json()

            return self._parse_result(data)

        except requests.RequestException as e:
            logger.error(f"Unpaywall API request failed for {doi}: {e}")
            return None

    def find_open_access(self, doi: str) -> UnpaywallResult | None:
        """Find open access information for a DOI.

        Args:
            doi: DOI to look up.

        Returns:
            UnpaywallResult or None if not found.
        """
        return self.get_oa_status(doi)

    def get_oa_status_batch(self, dois: list[str]) -> dict[str, UnpaywallResult]:
        """Get open access status for multiple DOIs.

        Args:
            dois: List of DOIs to look up

        Returns:
            Dictionary mapping DOI to UnpaywallResult
        """
        results = {}
        for doi in dois:
            result = self.get_oa_status(doi)
            if result:
                results[doi] = result
        return results

    def _parse_result(self, data: dict[str, Any]) -> UnpaywallResult:
        """Parse Unpaywall API response."""
        doi = data.get("doi", "")
        is_oa = data.get("is_oa", False)

        # Parse best OA location
        best_oa = None
        best_loc_data = data.get("best_oa_location")
        if best_loc_data:
            best_oa = self._parse_location(best_loc_data)

        # Parse all OA locations
        oa_locations = []
        for loc_data in data.get("oa_locations", []):
            loc = self._parse_location(loc_data)
            if loc:
                oa_locations.append(loc)

        return UnpaywallResult(
            doi=doi,
            is_oa=is_oa,
            title=data.get("title"),
            best_oa_location=best_oa,
            oa_locations=oa_locations,
            oa_status=data.get("oa_status"),
            publisher=data.get("publisher"),
            journal=data.get("journal_name"),
        )

    def _parse_location(self, loc_data: dict[str, Any]) -> OALocation | None:
        """Parse an OA location."""
        url = loc_data.get("url_for_pdf") or loc_data.get("url")
        if not url:
            return None

        return OALocation(
            url=url,
            is_pdf=bool(loc_data.get("url_for_pdf")),
            version=loc_data.get("version"),
            host_type=loc_data.get("host_type"),
            license=loc_data.get("license"),
        )
