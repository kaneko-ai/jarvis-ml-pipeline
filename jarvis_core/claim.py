"""Claim-based answer structure for evidence-based QA.

This module provides:
- Claim: A single statement with its supporting evidence
- ClaimSet: Collection of claims forming an answer
- ReviewNote: Collaborative review comment (RP27)

Per RP13, this enables claim-level citation verification,
ensuring each statement in an answer is backed by evidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class ReviewNote:
    """A review note on a claim.

    Per RP27, this enables collaborative review.

    Attributes:
        author: Who wrote the note.
        note_type: Type of note (comment, challenge, todo).
        text: The note content.
        created_at: When the note was created.
    """

    author: str
    note_type: Literal["comment", "challenge", "todo"]
    text: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "author": self.author,
            "note_type": self.note_type,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ReviewNote:
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            author=data["author"],
            note_type=data["note_type"],
            text=data["text"],
            created_at=created_at,
        )


@dataclass
class Claim:
    """A single claim/statement with supporting evidence.

    Attributes:
        id: Unique identifier for the claim.
        text: The claim text.
        citations: List of chunk_ids supporting this claim.
        valid: Whether the claim has valid evidence (set by Engine).
        validation_notes: Notes from validation (e.g., "missing evidence").
        reviews: List of review notes (RP27).
    """

    id: str
    text: str
    citations: list[str] = field(default_factory=list)
    valid: bool = True
    validation_notes: list[str] = field(default_factory=list)
    reviews: list[ReviewNote] = field(default_factory=list)

    @classmethod
    def create(cls, text: str, citations: list[str] | None = None) -> Claim:
        """Create a new claim with auto-generated ID.

        Args:
            text: The claim text.
            citations: Optional list of supporting chunk_ids.

        Returns:
            New Claim instance.
        """
        return cls(
            id=f"claim_{uuid.uuid4().hex[:8]}",
            text=text.strip(),
            citations=citations or [],
        )

    def add_review(
        self,
        author: str,
        text: str,
        note_type: Literal["comment", "challenge", "todo"] = "comment",
    ) -> ReviewNote:
        """Add a review note to this claim.

        Args:
            author: Who is adding the note.
            text: The note content.
            note_type: Type of note.

        Returns:
            The created ReviewNote.
        """
        note = ReviewNote(author=author, note_type=note_type, text=text)
        self.reviews.append(note)
        return note

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "citations": self.citations,
            "valid": self.valid,
            "validation_notes": self.validation_notes,
            "reviews": [r.to_dict() for r in self.reviews],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Claim:
        """Create from dictionary."""
        reviews = [ReviewNote.from_dict(r) for r in data.get("reviews", [])]
        return cls(
            id=data.get("id", f"claim_{uuid.uuid4().hex[:8]}"),
            text=data["text"],
            citations=data.get("citations", []),
            valid=data.get("valid", True),
            validation_notes=data.get("validation_notes", []),
            reviews=reviews,
        )


@dataclass
class ClaimSet:
    """A collection of claims forming an answer.

    Attributes:
        claims: List of Claim objects.
    """

    claims: list[Claim] = field(default_factory=list)

    def add(self, claim: Claim) -> None:
        """Add a claim to the set."""
        self.claims.append(claim)

    def add_new(self, text: str, citations: list[str] | None = None) -> Claim:
        """Create and add a new claim.

        Args:
            text: The claim text.
            citations: Optional list of supporting chunk_ids.

        Returns:
            The created Claim.
        """
        claim = Claim.create(text, citations)
        self.claims.append(claim)
        return claim

    def get_valid_claims(self) -> list[Claim]:
        """Get only valid claims."""
        return [c for c in self.claims if c.valid]

    def get_invalid_claims(self) -> list[Claim]:
        """Get only invalid claims."""
        return [c for c in self.claims if not c.valid]

    def get_all_citations(self) -> list[str]:
        """Get all unique chunk_ids from all claims."""
        all_ids: set[str] = set()
        for claim in self.claims:
            all_ids.update(claim.citations)
        return list(all_ids)

    def generate_answer(self, include_invalid: bool = False) -> str:
        """Generate answer text from claims.

        Args:
            include_invalid: If True, include invalid claims (with note).

        Returns:
            Combined answer text.
        """
        lines: list[str] = []

        for claim in self.claims:
            if claim.valid:
                lines.append(claim.text)
            elif include_invalid:
                lines.append(f"[Unverified] {claim.text}")

        return " ".join(lines)

    def has_any_valid(self) -> bool:
        """Check if there's at least one valid claim."""
        return any(c.valid for c in self.claims)

    def all_valid(self) -> bool:
        """Check if all claims are valid."""
        return all(c.valid for c in self.claims)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "claims": [c.to_dict() for c in self.claims],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ClaimSet:
        """Create from dictionary."""
        claims = [Claim.from_dict(c) for c in data.get("claims", [])]
        return cls(claims=claims)

    def __len__(self) -> int:
        return len(self.claims)

    def __iter__(self):
        return iter(self.claims)