"""Knowledge base utilities for Obsidian-compatible notes."""

from .indexer import ingest_run
from .weekly_pack import generate_weekly_pack

__all__ = ["ingest_run", "generate_weekly_pack"]
