"""PRISMA Schema.

Data models for PRISMA 2020 flow diagrams.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PRISMAStage(Enum):
    """Stages in PRISMA flow."""
    
    IDENTIFICATION = "identification"
    SCREENING = "screening"
    ELIGIBILITY = "eligibility"
    INCLUDED = "included"


@dataclass
class ExclusionReason:
    """Reason for excluding records."""
    
    reason: str
    count: int
    stage: PRISMAStage = PRISMAStage.SCREENING


@dataclass
class PRISMAData:
    """PRISMA 2020 flow diagram data.
    
    Based on PRISMA 2020 statement for systematic reviews.
    """
    
    # Identification
    records_from_databases: int = 0
    records_from_registers: int = 0
    records_from_other_sources: int = 0
    duplicates_removed: int = 0
    
    # Screening
    records_screened: int = 0
    records_excluded_screening: int = 0
    
    # Eligibility
    reports_sought: int = 0
    reports_not_retrieved: int = 0
    reports_assessed: int = 0
    reports_excluded: int = 0
    
    # Included
    studies_included: int = 0
    reports_included: int = 0
    
    # Exclusion reasons
    exclusion_reasons: List[ExclusionReason] = field(default_factory=list)
    
    # Database sources
    database_sources: List[str] = field(default_factory=list)
    
    def calculate_totals(self) -> None:
        """Calculate derived totals."""
        total_identified = (
            self.records_from_databases +
            self.records_from_registers +
            self.records_from_other_sources
        )
        
        if self.records_screened == 0:
            self.records_screened = total_identified - self.duplicates_removed
        
        if self.reports_sought == 0:
            self.reports_sought = self.records_screened - self.records_excluded_screening
        
        if self.reports_assessed == 0:
            self.reports_assessed = self.reports_sought - self.reports_not_retrieved
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "identification": {
                "databases": self.records_from_databases,
                "registers": self.records_from_registers,
                "other_sources": self.records_from_other_sources,
                "duplicates_removed": self.duplicates_removed,
            },
            "screening": {
                "records_screened": self.records_screened,
                "records_excluded": self.records_excluded_screening,
            },
            "eligibility": {
                "reports_sought": self.reports_sought,
                "reports_not_retrieved": self.reports_not_retrieved,
                "reports_assessed": self.reports_assessed,
                "reports_excluded": self.reports_excluded,
            },
            "included": {
                "studies": self.studies_included,
                "reports": self.reports_included,
            },
            "exclusion_reasons": [
                {"reason": r.reason, "count": r.count, "stage": r.stage.value}
                for r in self.exclusion_reasons
            ],
            "database_sources": self.database_sources,
        }
