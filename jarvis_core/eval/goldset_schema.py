"""Goldset Schema.

Per V4-A01, this defines the Goldset schema for evaluation.
Format: JSONL with Claim/Fact/Evidence/Locator/Label.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class GoldsetLabel(Enum):
    """Labels for goldset entries."""

    FACT = "fact"  # Fully supported by evidence
    INFERENCE = "inference"  # Derived, explicitly marked as estimated
    UNSUPPORTED = "unsupported"  # Claim without evidence
    QUOTE = "quote"  # Direct quote from source


@dataclass
class GoldsetEntry:
    """A single goldset entry.

    Represents a claim with its expected label and evidence.
    """

    claim_id: str
    claim_text: str
    expected_label: GoldsetLabel
    evidence_text: str | None = None
    source_locator: str | None = None
    notes: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "expected_label": self.expected_label.value,
            "evidence_text": self.evidence_text,
            "source_locator": self.source_locator,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GoldsetEntry:
        return cls(
            claim_id=data["claim_id"],
            claim_text=data["claim_text"],
            expected_label=GoldsetLabel(data["expected_label"]),
            evidence_text=data.get("evidence_text"),
            source_locator=data.get("source_locator"),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {}),
        )


def validate_goldset(entries: list[GoldsetEntry]) -> tuple[bool, list[str]]:
    """Validate a goldset.

    Args:
        entries: List of goldset entries.

    Returns:
        Tuple of (is_valid, list of issues).
    """
    issues = []

    claim_ids = set()
    for i, entry in enumerate(entries):
        # Check for duplicate IDs
        if entry.claim_id in claim_ids:
            issues.append(f"Duplicate claim_id: {entry.claim_id}")
        claim_ids.add(entry.claim_id)

        # FACT must have evidence
        if entry.expected_label == GoldsetLabel.FACT and not entry.evidence_text:
            issues.append(f"Entry {entry.claim_id}: FACT requires evidence_text")

        # QUOTE must have source
        if entry.expected_label == GoldsetLabel.QUOTE and not entry.source_locator:
            issues.append(f"Entry {entry.claim_id}: QUOTE requires source_locator")

        # Claim text must not be empty
        if not entry.claim_text.strip():
            issues.append(f"Entry {entry.claim_id}: empty claim_text")

    return len(issues) == 0, issues


def load_goldset(path: str) -> list[GoldsetEntry]:
    """Load goldset from JSONL file.

    Args:
        path: Path to JSONL file.

    Returns:
        List of goldset entries.
    """
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                entries.append(GoldsetEntry.from_dict(data))
    return entries


def save_goldset(entries: list[GoldsetEntry], path: str) -> None:
    """Save goldset to JSONL file.

    Args:
        entries: List of goldset entries.
        path: Output path.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")


def create_sample_goldset() -> list[GoldsetEntry]:
    """Create sample goldset for testing."""
    return [
        GoldsetEntry(
            claim_id="g001",
            claim_text="CD73 is expressed on tumor cells",
            expected_label=GoldsetLabel.FACT,
            evidence_text="CD73 expression was detected in 80% of tumor samples",
            source_locator="paper1.pdf:p5",
        ),
        GoldsetEntry(
            claim_id="g002",
            claim_text="CD73 may promote tumor growth",
            expected_label=GoldsetLabel.INFERENCE,
            evidence_text="Correlation between CD73 and tumor size was observed",
            source_locator="paper1.pdf:p12",
        ),
        GoldsetEntry(
            claim_id="g003",
            claim_text="CD73 inhibition is a promising therapy",
            expected_label=GoldsetLabel.UNSUPPORTED,
            notes="No direct evidence provided",
        ),
        GoldsetEntry(
            claim_id="g004",
            claim_text="CD73 is involved in adenosine metabolism",
            expected_label=GoldsetLabel.FACT,
            evidence_text="CD73 converts AMP to adenosine",
            source_locator="paper2.pdf:p3",
        ),
    ]
