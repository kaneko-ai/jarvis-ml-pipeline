"""JARVIS Citation Analysis Module.

Citation context extraction and stance classification.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.2
"""

from jarvis_core.citation.context_extractor import (
    CitationContext,
    extract_citation_contexts,
)
from jarvis_core.citation.stance_classifier import (
    CitationStance,
    StanceClassifier,
    classify_citation_stance,
)
from jarvis_core.citation.graph import CitationGraph, build_citation_graph

__all__ = [
    "CitationContext",
    "extract_citation_contexts",
    "CitationStance",
    "StanceClassifier",
    "classify_citation_stance",
    "CitationGraph",
    "build_citation_graph",
]
