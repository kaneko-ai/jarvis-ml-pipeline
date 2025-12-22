"""ClaimSet Diff.

Per RP-30, provides diff comparison for replay validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from ..artifacts import ClaimSet, Claim


@dataclass
class ClaimDiff:
    """Difference between two claims."""

    claim_id: str
    diff_type: str  # added, removed, changed
    original: str = ""
    new: str = ""
    citation_diff: List[Tuple[str, str]] = None  # (added/removed, chunk_id)

    def __post_init__(self):
        if self.citation_diff is None:
            self.citation_diff = []


@dataclass
class ClaimSetDiff:
    """Difference between two ClaimSets."""

    added: List[ClaimDiff]
    removed: List[ClaimDiff]
    changed: List[ClaimDiff]
    unchanged_count: int

    @property
    def is_identical(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def summary(self) -> str:
        if self.is_identical:
            return "Identical"
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return ", ".join(parts)


def diff_claimsets(original: ClaimSet, new: ClaimSet) -> ClaimSetDiff:
    """Compare two ClaimSets.

    Args:
        original: Original ClaimSet.
        new: New ClaimSet.

    Returns:
        ClaimSetDiff with added, removed, changed claims.
    """
    added = []
    removed = []
    changed = []
    unchanged = 0

    # Build maps by claim text (normalized)
    orig_map = {c.text.strip().lower(): c for c in original.claims}
    new_map = {c.text.strip().lower(): c for c in new.claims}

    # Find removed and changed
    for key, orig_claim in orig_map.items():
        if key not in new_map:
            removed.append(ClaimDiff(
                claim_id=orig_claim.claim_id,
                diff_type="removed",
                original=orig_claim.text,
            ))
        else:
            new_claim = new_map[key]
            # Check if citations changed
            orig_cites = set(orig_claim.citations)
            new_cites = set(new_claim.citations)

            if orig_cites != new_cites:
                citation_diff = []
                for c in new_cites - orig_cites:
                    citation_diff.append(("added", c))
                for c in orig_cites - new_cites:
                    citation_diff.append(("removed", c))

                changed.append(ClaimDiff(
                    claim_id=orig_claim.claim_id,
                    diff_type="changed",
                    original=orig_claim.text,
                    new=new_claim.text,
                    citation_diff=citation_diff,
                ))
            else:
                unchanged += 1

    # Find added
    for key, new_claim in new_map.items():
        if key not in orig_map:
            added.append(ClaimDiff(
                claim_id=new_claim.claim_id,
                diff_type="added",
                new=new_claim.text,
            ))

    return ClaimSetDiff(
        added=added,
        removed=removed,
        changed=changed,
        unchanged_count=unchanged,
    )
