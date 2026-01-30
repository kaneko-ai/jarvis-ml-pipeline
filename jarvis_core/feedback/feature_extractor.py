"""Feature extraction for feedback risk scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis_core.style.scientific_linter import ScientificLinter

SENTENCE_SPLIT = re.compile(r"[。\.\?!]+")
EVIDENCE_MARKERS = re.compile(
    r"\[(\d+)\]|\(([^)]+,\s*\d{4})\)|\b(according to|because|since|therefore)\b", re.I
)
CAUSAL_MARKERS = re.compile(r"\b(because|therefore|thus|hence)\b|ため|よって|従って", re.I)
AMBIGUOUS_TERMS = [
    "some",
    "many",
    "various",
    "significant",
    "possibly",
    "likely",
    "maybe",
    "ある程度",
    "いくつか",
    "多く",
    "様々",
    "重要",
    "可能性",
]


@dataclass
class FeatureRecord:
    location: dict[str, int]
    text: str
    features: dict[str, float]
    section: str


class FeedbackFeatureExtractor:
    """Extract paragraph/slide-level features."""

    def __init__(self, linter: ScientificLinter | None = None):
        self.linter = linter or ScientificLinter()

    def extract(self, text: str, section: str = "unknown") -> list[FeatureRecord]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        records: list[FeatureRecord] = []

        for idx, paragraph in enumerate(paragraphs, start=1):
            lint = self.linter.lint_text(paragraph)
            error_count = sum(1 for v in lint if v["severity"] == "error")
            warn_count = sum(1 for v in lint if v["severity"] == "warning")
            ambiguous_count = self._count_ambiguous(paragraph)
            evidence_matches = list(EVIDENCE_MARKERS.finditer(paragraph))
            evidence_count = len(evidence_matches)
            weak_evidence = 1.0 if evidence_count == 0 else 0.0
            avg_sentence_length = self._average_sentence_length(paragraph)
            subject_missing = (
                1.0 if not re.search(r"(\bwe\b|\bI\b|は|が)", paragraph, re.I) else 0.0
            )
            causal_present = 1.0 if CAUSAL_MARKERS.search(paragraph) else 0.0

            records.append(
                FeatureRecord(
                    location={"type": "paragraph", "index": idx},
                    text=paragraph,
                    section=section,
                    features={
                        "error_count": float(error_count),
                        "warn_count": float(warn_count),
                        "ambiguous_count": float(ambiguous_count),
                        "weak_evidence": float(weak_evidence),
                        "avg_sentence_length": float(avg_sentence_length),
                        "subject_missing": float(subject_missing),
                        "causal_present": float(causal_present),
                        "evidence_count": float(evidence_count),
                    },
                )
            )

        return records

    def _count_ambiguous(self, text: str) -> int:
        lowered = text.lower()
        return sum(lowered.count(term) for term in AMBIGUOUS_TERMS)

    def _average_sentence_length(self, text: str) -> float:
        sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
        if not sentences:
            return 0.0
        lengths = [len(s.split()) for s in sentences]
        return sum(lengths) / len(lengths)