"""PRISMA Flow Diagram Generator for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 2.4: PRISMA自動生成
Generates PRISMA 2020 flow diagrams for systematic reviews.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PRISMAStats:
    """PRISMA flow diagram statistics."""
    # Identification
    records_identified_database: int = 0
    records_identified_other: int = 0
    records_removed_duplicates: int = 0
    
    # Screening
    records_screened: int = 0
    records_excluded_title_abstract: int = 0
    
    # Eligibility
    reports_sought: int = 0
    reports_not_retrieved: int = 0
    reports_assessed: int = 0
    reports_excluded: int = 0
    exclusion_reasons: Dict[str, int] = field(default_factory=dict)
    
    # Included
    studies_included_review: int = 0
    studies_included_synthesis: int = 0
    
    def calculate_totals(self) -> None:
        """Calculate derived fields."""
        total_identified = self.records_identified_database + self.records_identified_other
        self.records_screened = total_identified - self.records_removed_duplicates
        self.reports_sought = self.records_screened - self.records_excluded_title_abstract
        self.reports_assessed = self.reports_sought - self.reports_not_retrieved
        self.studies_included_review = self.reports_assessed - self.reports_excluded


@dataclass
class PRISMADiagram:
    """PRISMA 2020 flow diagram representation."""
    title: str
    date: str
    stats: PRISMAStats
    databases_searched: List[str] = field(default_factory=list)
    other_sources: List[str] = field(default_factory=list)
    search_query: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "date": self.date,
            "stats": {
                "identification": {
                    "database": self.stats.records_identified_database,
                    "other": self.stats.records_identified_other,
                    "duplicates_removed": self.stats.records_removed_duplicates,
                },
                "screening": {
                    "screened": self.stats.records_screened,
                    "excluded": self.stats.records_excluded_title_abstract,
                },
                "eligibility": {
                    "sought": self.stats.reports_sought,
                    "not_retrieved": self.stats.reports_not_retrieved,
                    "assessed": self.stats.reports_assessed,
                    "excluded": self.stats.reports_excluded,
                    "exclusion_reasons": self.stats.exclusion_reasons,
                },
                "included": {
                    "review": self.stats.studies_included_review,
                    "synthesis": self.stats.studies_included_synthesis,
                },
            },
            "databases": self.databases_searched,
            "other_sources": self.other_sources,
        }


class PRISMAGenerator:
    """Generates PRISMA 2020 flow diagrams."""
    
    MERMAID_TEMPLATE = """
flowchart TD
    subgraph Identification
        A[Records identified from databases<br/>n = {db_records}] --> C
        B[Records from other sources<br/>n = {other_records}] --> C
        C[Records after duplicates removed<br/>n = {after_duplicates}]
    end
    
    subgraph Screening
        C --> D[Records screened<br/>n = {screened}]
        D --> E[Records excluded<br/>n = {excluded_screen}]
        D --> F[Reports sought for retrieval<br/>n = {sought}]
    end
    
    subgraph Eligibility
        F --> G[Reports not retrieved<br/>n = {not_retrieved}]
        F --> H[Reports assessed for eligibility<br/>n = {assessed}]
        H --> I[Reports excluded<br/>n = {excluded_elig}]
        H --> J[Studies included in review<br/>n = {included}]
    end
    
    subgraph Included
        J --> K[Studies included in synthesis<br/>n = {synthesis}]
    end
"""

    MARKDOWN_TEMPLATE = """# PRISMA 2020 Flow Diagram

**Title:** {title}  
**Date:** {date}

## Identification

| Source | Records |
|--------|---------|
| Database searching | {db_records} |
| Other sources | {other_records} |
| **Total** | **{total_records}** |
| Duplicates removed | {duplicates} |
| Records after duplicates | {after_duplicates} |

## Screening

| Stage | n |
|-------|---|
| Records screened | {screened} |
| Records excluded (title/abstract) | {excluded_screen} |

## Eligibility

| Stage | n |
|-------|---|
| Reports sought for retrieval | {sought} |
| Reports not retrieved | {not_retrieved} |
| Reports assessed for eligibility | {assessed} |
| Reports excluded (with reasons) | {excluded_elig} |

### Exclusion Reasons
{exclusion_reasons}

## Included

| Stage | n |
|-------|---|
| Studies included in review | {included} |
| Studies included in quantitative synthesis | {synthesis} |

---
*Generated by JARVIS Research OS*
"""

    def generate(
        self,
        stats: PRISMAStats,
        title: str = "Systematic Review",
        databases: Optional[List[str]] = None,
    ) -> PRISMADiagram:
        """Generate a PRISMA diagram from statistics."""
        stats.calculate_totals()
        
        return PRISMADiagram(
            title=title,
            date=datetime.now().strftime("%Y-%m-%d"),
            stats=stats,
            databases_searched=databases or ["PubMed", "Semantic Scholar", "OpenAlex"],
        )
    
    def to_mermaid(self, diagram: PRISMADiagram) -> str:
        """Generate Mermaid diagram code."""
        s = diagram.stats
        total = s.records_identified_database + s.records_identified_other
        
        return self.MERMAID_TEMPLATE.format(
            db_records=s.records_identified_database,
            other_records=s.records_identified_other,
            after_duplicates=total - s.records_removed_duplicates,
            screened=s.records_screened,
            excluded_screen=s.records_excluded_title_abstract,
            sought=s.reports_sought,
            not_retrieved=s.reports_not_retrieved,
            assessed=s.reports_assessed,
            excluded_elig=s.reports_excluded,
            included=s.studies_included_review,
            synthesis=s.studies_included_synthesis,
        )
    
    def to_markdown(self, diagram: PRISMADiagram) -> str:
        """Generate Markdown report."""
        s = diagram.stats
        total = s.records_identified_database + s.records_identified_other
        
        # Format exclusion reasons
        if s.exclusion_reasons:
            reasons = "\n".join(
                f"- {reason}: {count}" 
                for reason, count in s.exclusion_reasons.items()
            )
        else:
            reasons = "- No exclusion reasons recorded"
        
        return self.MARKDOWN_TEMPLATE.format(
            title=diagram.title,
            date=diagram.date,
            db_records=s.records_identified_database,
            other_records=s.records_identified_other,
            total_records=total,
            duplicates=s.records_removed_duplicates,
            after_duplicates=total - s.records_removed_duplicates,
            screened=s.records_screened,
            excluded_screen=s.records_excluded_title_abstract,
            sought=s.reports_sought,
            not_retrieved=s.reports_not_retrieved,
            assessed=s.reports_assessed,
            excluded_elig=s.reports_excluded,
            exclusion_reasons=reasons,
            included=s.studies_included_review,
            synthesis=s.studies_included_synthesis,
        )
    
    def from_pipeline_results(
        self,
        search_results: List[Dict],
        screened_results: List[Dict],
        included_results: List[Dict],
        title: str = "Systematic Review",
    ) -> PRISMADiagram:
        """Generate PRISMA from pipeline results."""
        # Calculate statistics from results
        total_searched = len(search_results)
        total_screened = len(screened_results)
        total_included = len(included_results)
        
        # Estimate duplicates (if same DOI)
        seen_dois = set()
        duplicates = 0
        for r in search_results:
            doi = r.get("doi")
            if doi:
                if doi in seen_dois:
                    duplicates += 1
                seen_dois.add(doi)
        
        stats = PRISMAStats(
            records_identified_database=total_searched,
            records_identified_other=0,
            records_removed_duplicates=duplicates,
            records_screened=total_searched - duplicates,
            records_excluded_title_abstract=total_searched - duplicates - total_screened,
            reports_sought=total_screened,
            reports_not_retrieved=0,
            reports_assessed=total_screened,
            reports_excluded=total_screened - total_included,
            studies_included_review=total_included,
            studies_included_synthesis=total_included,
        )
        
        return self.generate(stats, title)


def generate_prisma(
    search_results: List[Dict],
    screened_results: List[Dict],
    included_results: List[Dict],
    title: str = "Systematic Review",
    output_format: str = "markdown",
) -> str:
    """Convenience function to generate PRISMA output.
    
    Args:
        search_results: Initial search results.
        screened_results: Results after screening.
        included_results: Final included studies.
        title: Review title.
        output_format: 'markdown' or 'mermaid'.
        
    Returns:
        Formatted PRISMA output.
    """
    generator = PRISMAGenerator()
    diagram = generator.from_pipeline_results(
        search_results, screened_results, included_results, title
    )
    
    if output_format == "mermaid":
        return generator.to_mermaid(diagram)
    return generator.to_markdown(diagram)
