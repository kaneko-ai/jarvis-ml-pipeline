"""Query Understanding Module.

Per RP-304, parses and understands query intent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QueryType(Enum):
    """Types of research queries."""

    MECHANISM = "mechanism"  # How does X work?
    COMPARISON = "comparison"  # X vs Y
    TREATMENT = "treatment"  # How to treat X?
    CAUSAL = "causal"  # Does X cause Y?
    DEFINITION = "definition"  # What is X?
    REVIEW = "review"  # Overview of X
    SPECIFIC = "specific"  # Specific fact about X
    UNKNOWN = "unknown"


@dataclass
class ParsedEntity:
    """An extracted entity from query."""

    text: str
    entity_type: str  # gene, disease, drug, etc.
    normalized: str | None = None
    confidence: float = 1.0


@dataclass
class TimeRange:
    """Time range constraint."""

    start_year: int | None = None
    end_year: int | None = None
    description: str = ""


@dataclass
class ParsedQuery:
    """Result of query parsing."""

    original: str
    query_type: QueryType
    entities: list[ParsedEntity] = field(default_factory=list)
    time_range: TimeRange | None = None
    keywords: list[str] = field(default_factory=list)
    intent_description: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)


class QueryUnderstanding:
    """Parses and understands query intent.
    
    Per RP-304:
    - Classifies query type (comparison, mechanism, treatment, etc.)
    - Extracts entities (diseases, genes, drugs)
    - Parses time range (past 5 years, since 2020)
    """

    # Query type patterns
    TYPE_PATTERNS = [
        (r"(?i)\bhow\s+does\b|\bmechanism\b|\bpathway\b", QueryType.MECHANISM),
        (r"(?i)\bvs\.?\b|\bversus\b|\bcompared?\s+to\b|\bdifference\b", QueryType.COMPARISON),
        (r"(?i)\btreat(ment)?\b|\btherap(y|ies)\b|\bdrug\b", QueryType.TREATMENT),
        (r"(?i)\bcause[sd]?\b|\blead\s+to\b|\bresult\s+in\b", QueryType.CAUSAL),
        (r"(?i)\bwhat\s+is\b|\bdefine\b|\bdefinition\b", QueryType.DEFINITION),
        (r"(?i)\breview\b|\boverview\b|\bsummary\b|\bstate\s+of\b", QueryType.REVIEW),
    ]

    # Time range patterns
    TIME_PATTERNS = [
        (r"(?i)past\s+(\d+)\s+years?", "past_years"),
        (r"(?i)since\s+(\d{4})", "since_year"),
        (r"(?i)(\d{4})\s*[-–]\s*(\d{4})", "year_range"),
        (r"(?i)after\s+(\d{4})", "after_year"),
        (r"(?i)before\s+(\d{4})", "before_year"),
        (r"(?i)in\s+(\d{4})", "in_year"),
        (r"(?i)recent|latest|new", "recent"),
    ]

    # Entity patterns (simplified)
    ENTITY_PATTERNS = [
        (r"\b([A-Z][A-Z0-9]{2,})\b", "gene"),  # Gene symbols like CD73, EGFR
        (r"(?i)\b(cancer|tumor|carcinoma|lymphoma|leukemia)\b", "disease"),
        (r"(?i)\b(\w+inib|\w+mab|\w+zumab)\b", "drug"),  # Drug suffixes
    ]

    def __init__(self, current_year: int = 2024):
        self.current_year = current_year

    def parse(self, query: str) -> ParsedQuery:
        """Parse a query.
        
        Args:
            query: The search query.
            
        Returns:
            ParsedQuery with extracted information.
        """
        result = ParsedQuery(
            original=query,
            query_type=self._classify_type(query),
        )

        # Extract entities
        result.entities = self._extract_entities(query)

        # Parse time range
        result.time_range = self._parse_time_range(query)

        # Extract keywords
        result.keywords = self._extract_keywords(query)

        # Generate intent description
        result.intent_description = self._describe_intent(result)

        return result

    def _classify_type(self, query: str) -> QueryType:
        """Classify query type."""
        for pattern, query_type in self.TYPE_PATTERNS:
            if re.search(pattern, query):
                return query_type
        return QueryType.UNKNOWN

    def _extract_entities(self, query: str) -> list[ParsedEntity]:
        """Extract entities from query."""
        entities = []
        seen = set()

        for pattern, entity_type in self.ENTITY_PATTERNS:
            for match in re.finditer(pattern, query):
                text = match.group(1)
                if text.lower() not in seen:
                    seen.add(text.lower())
                    entities.append(ParsedEntity(
                        text=text,
                        entity_type=entity_type,
                    ))

        return entities

    def _parse_time_range(self, query: str) -> TimeRange | None:
        """Parse time range from query."""
        for pattern, range_type in self.TIME_PATTERNS:
            match = re.search(pattern, query)
            if match:
                if range_type == "past_years":
                    years = int(match.group(1))
                    return TimeRange(
                        start_year=self.current_year - years,
                        end_year=self.current_year,
                        description=f"Past {years} years",
                    )
                elif range_type == "since_year":
                    return TimeRange(
                        start_year=int(match.group(1)),
                        end_year=self.current_year,
                        description=f"Since {match.group(1)}",
                    )
                elif range_type == "year_range":
                    return TimeRange(
                        start_year=int(match.group(1)),
                        end_year=int(match.group(2)),
                        description=f"{match.group(1)}-{match.group(2)}",
                    )
                elif range_type == "after_year":
                    return TimeRange(
                        start_year=int(match.group(1)),
                        description=f"After {match.group(1)}",
                    )
                elif range_type == "before_year":
                    return TimeRange(
                        end_year=int(match.group(1)),
                        description=f"Before {match.group(1)}",
                    )
                elif range_type == "in_year":
                    year = int(match.group(1))
                    return TimeRange(
                        start_year=year,
                        end_year=year,
                        description=f"In {year}",
                    )
                elif range_type == "recent":
                    return TimeRange(
                        start_year=self.current_year - 3,
                        end_year=self.current_year,
                        description="Recent (past 3 years)",
                    )

        return None

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract important keywords."""
        # Remove stopwords and extract significant terms
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "and", "but", "or", "nor", "so", "yet", "both", "either",
            "neither", "not", "only", "own", "same", "than", "too",
            "very", "just", "what", "how", "why", "when", "where",
            "which", "who", "whom", "this", "that", "these", "those",
        }

        # Tokenize and filter
        words = re.findall(r"\b\w+\b", query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return list(dict.fromkeys(keywords))  # Dedupe while preserving order

    def _describe_intent(self, parsed: ParsedQuery) -> str:
        """Generate human-readable intent description."""
        parts = []

        # Query type
        type_desc = {
            QueryType.MECHANISM: "Understanding the mechanism of",
            QueryType.COMPARISON: "Comparing",
            QueryType.TREATMENT: "Finding treatments for",
            QueryType.CAUSAL: "Investigating causal relationship of",
            QueryType.DEFINITION: "Defining",
            QueryType.REVIEW: "Reviewing literature on",
            QueryType.SPECIFIC: "Finding specific information about",
            QueryType.UNKNOWN: "Searching for",
        }
        parts.append(type_desc.get(parsed.query_type, "Searching for"))

        # Entities
        if parsed.entities:
            entity_names = [e.text for e in parsed.entities[:3]]
            parts.append(", ".join(entity_names))

        # Time range
        if parsed.time_range:
            parts.append(f"({parsed.time_range.description})")

        return " ".join(parts)
