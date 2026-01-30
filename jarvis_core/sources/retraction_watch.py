"""Retraction Watch integration."""

from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass
class RetractionStatus:
    is_retracted: bool
    retraction_date: str | None
    reason: str | None
    source_url: str | None


def check_retraction(doi: str) -> RetractionStatus:
    """Check retraction status for a DOI using Retraction Watch API.

    This function gracefully degrades when the API is unavailable.
    """
    base_url = "https://api.retractionwatch.com/v1/retractions"
    source_url = f"{base_url}?doi={doi}"
    try:
        response = requests.get(source_url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if payload.get("count", 0) > 0:
            item = payload.get("results", [{}])[0]
            return RetractionStatus(
                is_retracted=True,
                retraction_date=item.get("retraction_date"),
                reason=item.get("reason"),
                source_url=item.get("url", source_url),
            )
    except requests.RequestException:
        return RetractionStatus(
            is_retracted=False, retraction_date=None, reason="unavailable", source_url=source_url
        )

    return RetractionStatus(
        is_retracted=False, retraction_date=None, reason=None, source_url=source_url
    )
