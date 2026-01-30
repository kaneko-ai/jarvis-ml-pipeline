"""Filtering helpers for retrieval results."""

from __future__ import annotations

from collections.abc import Iterable

from jarvis_core.retrieval.schema import Chunk


def _value_in(value, allowed):
    if allowed is None:
        return True
    return value in allowed


def _has_any(values: Iterable[str], allowed: list[str]) -> bool:
    if not allowed:
        return True
    return any(value in allowed for value in values)


def apply_filters(chunks: Iterable[Chunk], filters: dict) -> list[Chunk]:
    if not filters:
        return list(chunks)
    year_from = filters.get("year_from")
    year_to = filters.get("year_to")
    tier_in = filters.get("tier_in")
    oa_in = filters.get("oa_in")
    topics_any = filters.get("topics_any")
    source_type_in = filters.get("source_type_in")

    filtered = []
    for chunk in chunks:
        meta = chunk.meta
        if year_from is not None and (meta.year is None or meta.year < year_from):
            continue
        if year_to is not None and (meta.year is None or meta.year > year_to):
            continue
        if tier_in and not _value_in(meta.tier, tier_in):
            continue
        if oa_in and not _value_in(meta.oa, oa_in):
            continue
        if topics_any and not _has_any(meta.topics, topics_any):
            continue
        if source_type_in and chunk.source_type not in source_type_in:
            continue
        filtered.append(chunk)
    return filtered