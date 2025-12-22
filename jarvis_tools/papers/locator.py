"""Locator Contract.

Per RP-114, defines and validates locator requirements.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class LocatorType(Enum):
    """Types of locators."""

    PAGE = "page"
    SPAN = "span"
    SENTENCE = "sentence"
    SECTION = "section"
    CHUNK = "chunk"


@dataclass
class Locator:
    """A locator pointing to source content.

    At least one of: page, span, or sentence_id must be present.
    """

    source_id: str  # Paper/document ID
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    sentence_id_start: Optional[str] = None
    sentence_id_end: Optional[str] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if locator has required fields."""
        has_page = self.page_start is not None
        has_span = self.span_start is not None
        has_sentence = self.sentence_id_start is not None
        has_chunk = self.chunk_id is not None

        return has_page or has_span or has_sentence or has_chunk

    def get_type(self) -> LocatorType:
        """Get the primary locator type."""
        if self.sentence_id_start:
            return LocatorType.SENTENCE
        if self.span_start is not None:
            return LocatorType.SPAN
        if self.page_start is not None:
            return LocatorType.PAGE
        if self.chunk_id:
            return LocatorType.CHUNK
        return LocatorType.SECTION

    def to_string(self) -> str:
        """Convert to human-readable string."""
        parts = [self.source_id]

        if self.page_start is not None:
            if self.page_end and self.page_end != self.page_start:
                parts.append(f"pp.{self.page_start}-{self.page_end}")
            else:
                parts.append(f"p.{self.page_start}")

        if self.section:
            parts.append(f"§{self.section}")

        if self.sentence_id_start:
            if self.sentence_id_end and self.sentence_id_end != self.sentence_id_start:
                parts.append(f"s:{self.sentence_id_start}–{self.sentence_id_end}")
            else:
                parts.append(f"s:{self.sentence_id_start}")

        return ":".join(parts)

    @classmethod
    def parse(cls, locator_str: str) -> "Locator":
        """Parse a locator string."""
        parts = locator_str.split(":")
        source_id = parts[0] if parts else "unknown"

        locator = cls(source_id=source_id)

        for part in parts[1:]:
            # Page
            match = re.match(r"pp?\.(\d+)(?:-(\d+))?", part)
            if match:
                locator.page_start = int(match.group(1))
                if match.group(2):
                    locator.page_end = int(match.group(2))
                continue

            # Section
            if part.startswith("§"):
                locator.section = part[1:]
                continue

            # Sentence
            match = re.match(r"s:(.+?)(?:–(.+))?$", part)
            if match:
                locator.sentence_id_start = match.group(1)
                if match.group(2):
                    locator.sentence_id_end = match.group(2)

        return locator


@dataclass
class LocatorValidation:
    """Result of locator validation."""

    valid: bool
    warnings: List[str]
    missing_fields: List[str]


def validate_locator(locator: Locator) -> LocatorValidation:
    """Validate a locator against the contract.

    Contract (RP-114):
    - At least one of: page, span, sentence_id must be present
    - source_id is required
    """
    warnings = []
    missing = []

    if not locator.source_id or locator.source_id == "unknown":
        missing.append("source_id")
        warnings.append("Missing source_id")

    if not locator.is_valid():
        missing.append("location_info")
        warnings.append("Missing page/span/sentence_id - locator is incomplete")

    # Soft warnings
    if not locator.section:
        warnings.append("No section specified (recommended)")

    valid = len(missing) == 0

    return LocatorValidation(
        valid=valid,
        warnings=warnings,
        missing_fields=missing,
    )


def validate_locators(locators: List[Locator]) -> List[LocatorValidation]:
    """Validate multiple locators."""
    return [validate_locator(loc) for loc in locators]
