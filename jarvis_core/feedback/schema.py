"""Feedback schema definitions for P8 Feedback Intelligence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

VALID_SOURCES = {"email", "comment", "diff"}
VALID_REVIEWERS = {"kato_prof", "suzuki_sensei", "office", "unknown"}
VALID_DOCUMENT_TYPES = {"thesis", "slides", "plan", "draft"}
VALID_LOCATION_TYPES = {"paragraph", "sentence", "slide"}
VALID_CATEGORIES = {
    "terminology",
    "evidence",
    "logic",
    "expression",
    "figure",
    "conclusion",
    "format",
}
VALID_SEVERITIES = {"critical", "major", "minor"}
VALID_RESOLUTION_TYPES = {"rewrite", "add_citation", "delete", "restructure", "unknown"}


@dataclass
class FeedbackLocation:
    """Normalized location for feedback."""

    type: str
    index: int

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "index": self.index}


@dataclass
class FeedbackEntry:
    """Normalized feedback entry schema."""

    feedback_id: str
    source: str
    reviewer: str
    date: str
    document_type: str
    location: FeedbackLocation
    category: str
    severity: str
    message: str
    resolved: bool
    resolution_type: str
    notes: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "source": self.source,
            "reviewer": self.reviewer,
            "date": self.date,
            "document_type": self.document_type,
            "location": self.location.to_dict(),
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "resolved": self.resolved,
            "resolution_type": self.resolution_type,
            "notes": self.notes,
            "raw": self.raw,
        }


def _normalize_date(value: str | None) -> str:
    if value:
        return value
    return datetime.now().strftime("%Y-%m-%d")


def normalize_feedback(data: dict[str, Any]) -> FeedbackEntry:
    """Normalize raw feedback into schema.

    Args:
        data: Raw feedback dict.

    Returns:
        FeedbackEntry
    """
    location_data = data.get("location") or {}
    location = FeedbackLocation(
        type=location_data.get("type", "paragraph"),
        index=int(location_data.get("index", 0)),
    )
    entry = FeedbackEntry(
        feedback_id=data.get("feedback_id", "FB-UNKNOWN"),
        source=data.get("source", "comment"),
        reviewer=data.get("reviewer", "unknown"),
        date=_normalize_date(data.get("date")),
        document_type=data.get("document_type", "draft"),
        location=location,
        category=data.get("category", "expression"),
        severity=data.get("severity", "minor"),
        message=data.get("message", ""),
        resolved=bool(data.get("resolved", False)),
        resolution_type=data.get("resolution_type", "unknown"),
        notes=data.get("notes", ""),
        raw=data,
    )
    _validate_entry(entry)
    return entry


def _validate_entry(entry: FeedbackEntry) -> None:
    if entry.source not in VALID_SOURCES:
        raise ValueError(f"Invalid source: {entry.source}")
    if entry.reviewer not in VALID_REVIEWERS:
        raise ValueError(f"Invalid reviewer: {entry.reviewer}")
    if entry.document_type not in VALID_DOCUMENT_TYPES:
        raise ValueError(f"Invalid document type: {entry.document_type}")
    if entry.location.type not in VALID_LOCATION_TYPES:
        raise ValueError(f"Invalid location type: {entry.location.type}")
    if entry.category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {entry.category}")
    if entry.severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {entry.severity}")
    if entry.resolution_type not in VALID_RESOLUTION_TYPES:
        raise ValueError(f"Invalid resolution type: {entry.resolution_type}")
