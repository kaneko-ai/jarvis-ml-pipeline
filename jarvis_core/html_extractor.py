"""HTML text extractor for web content.

This module provides:
- extract_main_text(): Extract main body text from HTML
- extract_title(): Extract page title from HTML

Per RP8, this provides clean text extraction for EvidenceStore ingestion.
"""

from __future__ import annotations

import re

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# Tags to remove entirely (including content)
REMOVE_TAGS = [
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "iframe",
    "svg",
]


def extract_title(html: str) -> str | None:
    """Extract the page title from HTML.

    Args:
        html: HTML content.

    Returns:
        The page title, or None if not found.
    """
    if not HAS_BS4:
        # Fallback: simple regex
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text().strip()
    return None


def extract_main_text(html: str) -> str:
    """Extract main body text from HTML.

    Strategy (in order):
    1. Look for <article> tag
    2. Look for <main> tag
    3. Fall back to <body> with unwanted elements removed

    Args:
        html: HTML content.

    Returns:
        Extracted text content, cleaned and normalized.
    """
    if not HAS_BS4:
        # Very basic fallback without BeautifulSoup
        return _extract_text_regex(html)

    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags first
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Try to find main content container
    main_content = None

    # Strategy 1: <article>
    article = soup.find("article")
    if article:
        main_content = article

    # Strategy 2: <main>
    if main_content is None:
        main = soup.find("main")
        if main:
            main_content = main

    # Strategy 3: <body>
    if main_content is None:
        main_content = soup.find("body")

    if main_content is None:
        main_content = soup

    # Extract and clean text
    text = main_content.get_text(separator="\n")
    return _normalize_text(text)


def _extract_text_regex(html: str) -> str:
    """Fallback text extraction using regex (no BeautifulSoup)."""
    # Remove script/style content
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove all HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')

    return _normalize_text(text)


def _normalize_text(text: str) -> str:
    """Normalize whitespace in extracted text."""
    # Replace multiple spaces with single space
    text = re.sub(r"[ \t]+", " ", text)

    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]

    # Remove empty lines at start and end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    return "\n".join(lines)