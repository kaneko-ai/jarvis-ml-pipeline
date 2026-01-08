"""Web fetcher for URL-based evidence ingestion.

This module provides:
- fetch_url(): Fetch HTML from URL with proper headers
- FetchResult: Metadata about the fetch operation

Per RP8, this creates the standard entry point for ingesting
web content into EvidenceStore.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger("jarvis_core.web_fetcher")

# Standard User-Agent to avoid blocking
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Jarvis/1.0"
)


@dataclass
class FetchMeta:
    """Metadata about a URL fetch operation."""

    final_url: str
    status_code: int
    content_type: str
    is_pdf: bool = False


class FetchError(Exception):
    """Raised when URL fetch fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def fetch_url(
    url: str,
    timeout_sec: int = 15,
    user_agent: str = DEFAULT_USER_AGENT,
) -> tuple[str, FetchMeta]:
    """Fetch HTML content from a URL.

    Args:
        url: The URL to fetch.
        timeout_sec: Request timeout in seconds.
        user_agent: User-Agent header value.

    Returns:
        Tuple of (html_content, FetchMeta).

    Raises:
        FetchError: If the request fails or returns non-HTML content.
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.Timeout as e:
        raise FetchError(f"Request timed out: {url}") from e
    except requests.RequestException as e:
        status = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        raise FetchError(f"Request failed: {e}", status_code=status) from e

    content_type = response.headers.get("Content-Type", "").lower()
    final_url = response.url  # After redirects

    meta = FetchMeta(
        final_url=final_url,
        status_code=response.status_code,
        content_type=content_type,
        is_pdf="application/pdf" in content_type,
    )

    # Check for PDF - caller should handle this
    if meta.is_pdf:
        logger.info("URL returned PDF content: %s", url)
        return "", meta

    # Check for HTML content
    if not any(t in content_type for t in ["text/html", "application/xhtml"]):
        raise FetchError(
            f"Unsupported content type: {content_type}",
            status_code=response.status_code,
        )

    # Return HTML content
    return response.text, meta


def load_url_as_document(
    url: str,
    html: str | None = None,
    meta: FetchMeta | None = None,
) -> SourceDocument:
    """Load a URL as a SourceDocument.

    Args:
        url: The URL to load.
        html: Pre-fetched HTML content (optional).
        meta: Pre-fetched metadata (optional).

    Returns:
        SourceDocument ready for ingestion.

    Raises:
        FetchError: If fetch fails.
    """
    from .html_extractor import extract_main_text, extract_title
    from .sources import SourceDocument

    if html is None or meta is None:
        html, meta = fetch_url(url)

    if meta.is_pdf:
        raise FetchError(
            "URL returned PDF content. Use ingest_pdf instead.",
            status_code=meta.status_code,
        )

    text = extract_main_text(html)
    title = extract_title(html)

    return SourceDocument(
        source="url",
        locator_base=f"url:{meta.final_url}",
        text=text,
        metadata={
            "title": title,
            "final_url": meta.final_url,
            "content_type": meta.content_type,
        },
    )


def ingest_url(
    url: str,
    store: EvidenceStore,
    context: ExecutionContext | None = None,
) -> list[ChunkResult]:
    """Convenience function to ingest a URL into EvidenceStore.

    This handles both HTML and PDF URLs:
    - HTML: fetch → extract → chunk → store
    - PDF: delegate to ingest_pdf

    Args:
        url: The URL to ingest.
        store: The EvidenceStore to populate.
        context: Optional ExecutionContext to register chunks in.

    Returns:
        List of ChunkResults from the URL.

    Raises:
        FetchError: If fetch fails (non-PDF, non-HTML).
    """
    from .sources import ingest

    # Fetch the URL
    html, meta = fetch_url(url)

    # Handle PDF URLs
    if meta.is_pdf:
        logger.info("URL is PDF, delegating to PDF ingest: %s", url)
        # For PDF URLs, we need to download and process
        # MVP: raise error, user should download PDF first
        raise FetchError(
            "PDF URL detected. Download the PDF and use ingest_pdf().",
            status_code=meta.status_code,
        )

    # Load as document and ingest
    doc = load_url_as_document(url, html=html, meta=meta)
    results = ingest(doc, store)

    # Add URL info to previews
    for result in results:
        result.preview = f"[url] {result.preview}"

    if context is not None:
        context.add_chunks(results)

    return results
