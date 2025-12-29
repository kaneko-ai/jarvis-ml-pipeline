"""Deduplicate KB content."""
from __future__ import annotations

from typing import Iterable, List, Mapping


def dedup_claims(claims: Iterable[Mapping]) -> List[Mapping]:
    seen = set()
    unique = []
    for claim in claims:
        key = (claim.get("claim_id") or "", claim.get("claim_text") or "")
        if key in seen:
            continue
        seen.add(key)
        unique.append(claim)
    return unique
