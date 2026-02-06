"""Pretrain meta core helpers."""

from __future__ import annotations


def build_meta_core(metadata: dict) -> dict:
    """Build a meta core payload.

    Args:
        metadata: Input metadata.

    Returns:
        Normalized metadata dictionary.
    """
    return dict(metadata)


__all__ = ["build_meta_core"]
