"""Sectionizer.

Per RP-111, detects IMRaD sections in scientific papers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class SectionType(Enum):
    """Section types in scientific papers."""

    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    FIGURE = "figure"
    TABLE = "table"
    SUPPLEMENTARY = "supplementary"
    OTHER = "other"


# Section header patterns
SECTION_PATTERNS = {
    SectionType.ABSTRACT: [r"^\s*abstract\s*$", r"^\s*summary\s*$"],
    SectionType.INTRODUCTION: [r"^\s*introduction\s*$", r"^\s*background\s*$"],
    SectionType.METHODS: [
        r"^\s*methods?\s*$",
        r"^\s*materials?\s+and\s+methods?\s*$",
        r"^\s*experimental\s+procedures?\s*$",
    ],
    SectionType.RESULTS: [r"^\s*results?\s*$", r"^\s*findings?\s*$"],
    SectionType.DISCUSSION: [r"^\s*discussion\s*$"],
    SectionType.CONCLUSION: [r"^\s*conclusions?\s*$"],
    SectionType.REFERENCES: [
        r"^\s*references?\s*$",
        r"^\s*bibliography\s*$",
        r"^\s*cited\s+literature\s*$",
    ],
    SectionType.FIGURE: [r"^\s*figure\s+\d+", r"^\s*fig\.?\s+\d+"],
    SectionType.TABLE: [r"^\s*table\s+\d+"],
    SectionType.SUPPLEMENTARY: [
        r"^\s*supplementary\s*",
        r"^\s*supporting\s+information\s*",
    ],
}


@dataclass
class Section:
    """A detected section."""

    section_type: SectionType
    title: str
    start_line: int
    end_line: int
    content: str

    @property
    def section_name(self) -> str:
        return self.section_type.value


def detect_section_type(line: str) -> Optional[SectionType]:
    """Detect section type from a line."""
    line_lower = line.lower().strip()

    for section_type, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, line_lower, re.IGNORECASE):
                return section_type

    return None


def is_section_header(line: str) -> bool:
    """Check if a line is likely a section header."""
    line = line.strip()

    # Empty line
    if not line:
        return False

    # Too long for header
    if len(line) > 100:
        return False

    # All caps or title case with known patterns
    if line.isupper() and 3 <= len(line) <= 50:
        return True

    # Known section pattern
    if detect_section_type(line) is not None:
        return True

    # Numbered section (1., 2., etc.)
    if re.match(r"^\d+\.?\s+[A-Z]", line):
        return True

    return False


def sectionize(text: str) -> List[Section]:
    """Split text into sections.

    Args:
        text: Full text of a paper.

    Returns:
        List of Section objects.
    """
    lines = text.split("\n")
    sections: List[Section] = []

    current_type = SectionType.OTHER
    current_title = "Preamble"
    current_start = 0
    current_lines: List[str] = []

    for i, line in enumerate(lines):
        if is_section_header(line):
            # Save previous section
            if current_lines or current_start < i:
                sections.append(
                    Section(
                        section_type=current_type,
                        title=current_title,
                        start_line=current_start,
                        end_line=i - 1,
                        content="\n".join(current_lines),
                    )
                )

            # Start new section
            detected = detect_section_type(line)
            current_type = detected if detected else SectionType.OTHER
            current_title = line.strip()
            current_start = i
            current_lines = []
        else:
            current_lines.append(line)

    # Save final section
    if current_lines:
        sections.append(
            Section(
                section_type=current_type,
                title=current_title,
                start_line=current_start,
                end_line=len(lines) - 1,
                content="\n".join(current_lines),
            )
        )

    return sections


def get_section_by_type(sections: List[Section], section_type: SectionType) -> Optional[Section]:
    """Get first section of a given type."""
    for section in sections:
        if section.section_type == section_type:
            return section
    return None
