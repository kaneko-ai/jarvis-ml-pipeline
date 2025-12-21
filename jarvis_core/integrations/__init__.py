"""Integrations package for knowledge management tools.

Provides exporters for:
- NotebookLM
- Obsidian
- Notion
- Watch mode
"""
from .obsidian_sync import sync_to_obsidian, ObsidianSync
from .watch import watch_manifest, ManifestWatcher

__all__ = [
    "sync_to_obsidian",
    "ObsidianSync",
    "watch_manifest",
    "ManifestWatcher",
]
