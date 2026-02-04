"""PRISMA 2020 Compliance Module.

Implements checklist verification for systematic reviews.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.6
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PRISMASection(str, Enum):
    TITLE = "title"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    OTHER = "other"


class PRISMAItem(BaseModel):
    item_number: str
    description: str
    section: PRISMASection
    is_compliant: bool = False
    details: Optional[str] = None
    location: Optional[str] = None


class PRISMAChecklist(BaseModel):
    version: str = "2020"
    items: List[PRISMAItem] = Field(default_factory=list)

    def compliance_score(self) -> float:
        if not self.items:
            return 0.0
        compliant_count = sum(1 for item in self.items if item.is_compliant)
        return compliant_count / len(self.items)


def get_prisma_2020_template() -> PRISMAChecklist:
    """Generate a template checklist for PRISMA 2020."""
    return PRISMAChecklist(
        items=[
            PRISMAItem(
                item_number="1",
                description="Identify the report as a systematic review in the title.",
                section=PRISMASection.TITLE,
            ),
            PRISMAItem(
                item_number="2",
                description="See the PRISMA 2020 for Abstracts checklist.",
                section=PRISMASection.ABSTRACT,
            ),
            # Add more items as needed for Phase 3 parity
        ]
    )


class PRISMAValidator:
    """Validates research reports against PRISMA checklist."""

    def __init__(self):
        self.template = get_prisma_2020_template()

    def validate_text(self, title: str, text: str) -> PRISMAChecklist:
        """Heuristic validation of PRISMA items based on text content."""
        checklist = get_prisma_2020_template()

        # Item 1: Title check
        if "systematic review" in title.lower():
            checklist.items[0].is_compliant = True
            checklist.items[0].details = "Found 'systematic review' in title."

        return checklist
