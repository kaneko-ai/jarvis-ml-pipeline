"""PRISMA 2020 Compliance Module for Systematic Reviews."""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

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
    """Returns a basic template for PRISMA 2020 checklist."""
    items = [
        PRISMAItem(item_number="1", description="Title", section=PRISMASection.TITLE),
        PRISMAItem(item_number="2", description="Structured summary", section=PRISMASection.ABSTRACT),
        PRISMAItem(item_number="3", description="Rationale", section=PRISMASection.INTRODUCTION),
        PRISMAItem(item_number="4", description="Objectives", section=PRISMASection.INTRODUCTION),
        PRISMAItem(item_number="5", description="Eligibility criteria", section=PRISMASection.METHODS),
        PRISMAItem(item_number="6", description="Information sources", section=PRISMASection.METHODS),
        PRISMAItem(item_number="7", description="Search strategy", section=PRISMASection.METHODS),
        # Add more items as needed for S-level evaluation
    ]
    return PRISMAChecklist(items=items)

class PRISMAValidator:
    """Validator for PRISMA 2020 compliance."""
    
    def validate_report(self, report_text: str) -> PRISMAChecklist:
        """Simple rule-based validation of a research report against PRISMA items."""
        checklist = get_prisma_2020_template()
        # In a real system, this would use an LLM or NLP to find the items
        for item in checklist.items:
            if item.description.lower() in report_text.lower():
                item.is_compliant = True
                item.details = f"Found keyword matching '{item.description}'"
        return checklist
