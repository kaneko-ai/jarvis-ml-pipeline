"""HTML Extract.

Per RP-105, extracts text from HTML as PDF fallback.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class HTMLExtractResult:
    """Result of HTML extraction."""

    text: str
    title: Optional[str]
    abstract: Optional[str]
    sections: List[Tuple[str, str]]  # (heading, content)
    source: str = "html_fallback"
    method: str = "html.parser"


class ScientificHTMLParser(HTMLParser):
    """Parser for scientific paper HTML."""

    def __init__(self):
        super().__init__()
        self._text_parts: List[str] = []
        self._title: Optional[str] = None
        self._abstract: Optional[str] = None
        self._current_tag: str = ""
        self._in_abstract: bool = False
        self._in_title: bool = False
        self._in_script: bool = False
        self._in_style: bool = False

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        attrs_dict = dict(attrs)

        if tag == "title":
            self._in_title = True
        elif tag == "script":
            self._in_script = True
        elif tag == "style":
            self._in_style = True
        elif tag in ("p", "div", "section"):
            # Check for abstract class/id
            class_attr = attrs_dict.get("class", "").lower()
            id_attr = attrs_dict.get("id", "").lower()
            if "abstract" in class_attr or "abstract" in id_attr:
                self._in_abstract = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_script = False
        elif tag == "style":
            self._in_style = False
        elif tag in ("p", "div", "section"):
            if self._in_abstract:
                self._in_abstract = False

        self._current_tag = ""

    def handle_data(self, data):
        if self._in_script or self._in_style:
            return

        text = data.strip()
        if not text:
            return

        if self._in_title and not self._title:
            self._title = text
        elif self._in_abstract:
            if self._abstract:
                self._abstract += " " + text
            else:
                self._abstract = text
        else:
            self._text_parts.append(text)

    def get_result(self) -> HTMLExtractResult:
        """Get extraction result."""
        full_text = " ".join(self._text_parts)

        return HTMLExtractResult(
            text=full_text,
            title=self._title,
            abstract=self._abstract,
            sections=[],
        )


def extract_from_html(html: str) -> HTMLExtractResult:
    """Extract text from HTML.

    Args:
        html: HTML content.

    Returns:
        HTMLExtractResult with extracted text.
    """
    parser = ScientificHTMLParser()

    try:
        parser.feed(html)
    except Exception:
        # Fallback: strip all tags
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return HTMLExtractResult(
            text=text,
            title=None,
            abstract=None,
            sections=[],
            method="regex_fallback",
        )

    return parser.get_result()


def extract_abstract_like(html: str) -> Optional[str]:
    """Extract abstract or first substantial paragraph.

    Args:
        html: HTML content.

    Returns:
        Abstract text or None.
    """
    result = extract_from_html(html)

    if result.abstract:
        return result.abstract

    # Try to find abstract-like content
    text = result.text

    # Look for "Abstract" section
    abstract_match = re.search(
        r"(?:Abstract|Summary)[\s:]*(.{100,1000}?)(?:Introduction|\n\n|Keywords)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if abstract_match:
        return abstract_match.group(1).strip()

    # Return first 500 chars as fallback
    if len(text) > 100:
        return text[:500] + "..."

    return None
