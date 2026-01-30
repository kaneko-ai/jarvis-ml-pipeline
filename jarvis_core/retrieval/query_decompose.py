"""Query Decomposition.

Per RP-121, decomposes queries into sub-queries for better retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class QueryCategory(Enum):
    """Immunology query categories (S1-S5)."""

    S1_BASIC = "S1"  # Basic concept
    S2_MECHANISM = "S2"  # Mechanism/pathway
    S3_CLINICAL = "S3"  # Clinical application
    S4_COMPARISON = "S4"  # Comparison of entities
    S5_REVIEW = "S5"  # Review/synthesis


@dataclass
class DecomposedQuery:
    """A decomposed query with sub-queries."""

    original: str
    category: QueryCategory
    sub_queries: list[str]
    entities: list[str]
    confidence: float


# Category detection patterns
CATEGORY_PATTERNS = {
    QueryCategory.S1_BASIC: [
        r"\bwhat is\b",
        r"\bdefine\b",
        r"\bdefinition of\b",
        r"\bwhat are\b",
    ],
    QueryCategory.S2_MECHANISM: [
        r"\bhow does\b",
        r"\bmechanism\b",
        r"\bpathway\b",
        r"\bsignaling\b",
        r"\bregulat",
    ],
    QueryCategory.S3_CLINICAL: [
        r"\btreatment\b",
        r"\btherapy\b",
        r"\bclinical\b",
        r"\bpatient\b",
        r"\btrial\b",
    ],
    QueryCategory.S4_COMPARISON: [
        r"\bcompare\b",
        r"\bvs\.?\b",
        r"\bversus\b",
        r"\bdifference\b",
        r"\bsimilar",
    ],
    QueryCategory.S5_REVIEW: [
        r"\breview\b",
        r"\bsummary\b",
        r"\boverview\b",
        r"\bcurrent state\b",
    ],
}

# Known immunology entities
KNOWN_ENTITIES = [
    "CD73",
    "NT5E",
    "CD39",
    "ENTPD1",
    "PD-1",
    "PDCD1",
    "PD-L1",
    "CD274",
    "CTLA-4",
    "TIM-3",
    "LAG-3",
    "TIGIT",
    "adenosine",
    "ATP",
    "AMP",
    "Treg",
    "Th1",
    "Th2",
    "Th17",
    "TME",
    "tumor microenvironment",
    "checkpoint",
    "immunotherapy",
]


def detect_category(query: str) -> tuple[QueryCategory, float]:
    """Detect query category using rules."""
    query_lower = query.lower()

    best_category = QueryCategory.S1_BASIC
    best_score = 0.0

    for category, patterns in CATEGORY_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, query_lower))
        score = matches / len(patterns)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category, max(0.3, best_score)


def extract_entities(query: str) -> list[str]:
    """Extract known entities from query."""
    entities = []
    query_upper = query.upper()

    for entity in KNOWN_ENTITIES:
        if entity.upper() in query_upper:
            entities.append(entity)

    return entities


def generate_sub_queries(
    query: str,
    category: QueryCategory,
    entities: list[str],
) -> list[str]:
    """Generate sub-queries based on category and entities."""
    sub_queries = [query]  # Always include original

    if category == QueryCategory.S1_BASIC:
        # Add definition queries for each entity
        for entity in entities[:2]:
            sub_queries.append(f"{entity} function definition")
            sub_queries.append(f"{entity} expression")

    elif category == QueryCategory.S2_MECHANISM:
        # Add pathway queries
        for entity in entities[:2]:
            sub_queries.append(f"{entity} signaling pathway")
            sub_queries.append(f"{entity} regulation mechanism")

    elif category == QueryCategory.S3_CLINICAL:
        # Add clinical queries
        for entity in entities[:2]:
            sub_queries.append(f"{entity} clinical trials")
            sub_queries.append(f"{entity} therapeutic target")

    elif category == QueryCategory.S4_COMPARISON:
        # Add individual entity queries
        for entity in entities:
            sub_queries.append(f"{entity} function")

    elif category == QueryCategory.S5_REVIEW:
        # Add recent review queries
        for entity in entities[:2]:
            sub_queries.append(f"{entity} review recent")

    return sub_queries[:5]  # Limit to 5 sub-queries


def decompose_query(query: str) -> DecomposedQuery:
    """Decompose a query into sub-queries.

    Args:
        query: Original query.

    Returns:
        DecomposedQuery with category, sub-queries, and entities.
    """
    category, confidence = detect_category(query)
    entities = extract_entities(query)
    sub_queries = generate_sub_queries(query, category, entities)

    return DecomposedQuery(
        original=query,
        category=category,
        sub_queries=sub_queries,
        entities=entities,
        confidence=confidence,
    )