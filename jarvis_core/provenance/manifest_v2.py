"""Manifest V2.

Per V4-B03, this records all execution parameters for reproducibility.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class ManifestV2:
    """Execution manifest for reproducibility."""

    # Identification
    run_id: str
    created_at: datetime

    # Query info
    query: str = ""
    concepts: List[str] = field(default_factory=list)

    # Inputs
    input_hashes: List[str] = field(default_factory=list)
    input_sources: List[str] = field(default_factory=list)

    # Tool versions
    jarvis_version: str = "4.1"
    llm_model: str = ""
    llm_version: str = ""
    extractor_version: str = ""

    # Parameters
    thresholds: Dict[str, float] = field(default_factory=dict)
    config_hash: str = ""

    # Outputs
    output_hashes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "query": self.query,
            "concepts": self.concepts,
            "input_hashes": self.input_hashes,
            "input_sources": self.input_sources,
            "jarvis_version": self.jarvis_version,
            "llm_model": self.llm_model,
            "llm_version": self.llm_version,
            "extractor_version": self.extractor_version,
            "thresholds": self.thresholds,
            "config_hash": self.config_hash,
            "output_hashes": self.output_hashes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ManifestV2":
        return cls(
            run_id=data["run_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            query=data.get("query", ""),
            concepts=data.get("concepts", []),
            input_hashes=data.get("input_hashes", []),
            input_sources=data.get("input_sources", []),
            jarvis_version=data.get("jarvis_version", "4.1"),
            llm_model=data.get("llm_model", ""),
            llm_version=data.get("llm_version", ""),
            extractor_version=data.get("extractor_version", ""),
            thresholds=data.get("thresholds", {}),
            config_hash=data.get("config_hash", ""),
            output_hashes=data.get("output_hashes", []),
        )

    def save(self, path: str) -> None:
        """Save manifest to JSON."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "ManifestV2":
        """Load manifest from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


def create_manifest(
    query: str = "",
    concepts: List[str] = None,
    inputs: List[str] = None,
    config: dict = None,
) -> ManifestV2:
    """Create a new manifest.

    Args:
        query: Research query.
        concepts: Focus concepts.
        inputs: Input file paths.
        config: Configuration dict.

    Returns:
        New ManifestV2 instance.
    """
    from ..store.content_addressed import compute_hash

    manifest = ManifestV2(
        run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        created_at=datetime.now(),
        query=query,
        concepts=concepts or [],
        input_sources=inputs or [],
    )

    # Compute input hashes
    for inp in (inputs or []):
        path = Path(inp)
        if path.exists():
            content = path.read_bytes()
            manifest.input_hashes.append(compute_hash(content))

    # Compute config hash
    if config:
        manifest.config_hash = compute_hash(json.dumps(config, sort_keys=True))

    return manifest


def compare_manifests(m1: ManifestV2, m2: ManifestV2) -> Dict[str, str]:
    """Compare two manifests and return differences.

    Args:
        m1: First manifest.
        m2: Second manifest.

    Returns:
        Dict of field -> change description.
    """
    diffs = {}

    if m1.input_hashes != m2.input_hashes:
        diffs["inputs"] = f"Inputs changed: {len(m1.input_hashes)} → {len(m2.input_hashes)}"

    if m1.llm_model != m2.llm_model:
        diffs["llm_model"] = f"Model changed: {m1.llm_model} → {m2.llm_model}"

    if m1.thresholds != m2.thresholds:
        diffs["thresholds"] = f"Thresholds changed"

    if m1.config_hash != m2.config_hash:
        diffs["config"] = "Configuration changed"

    if m1.jarvis_version != m2.jarvis_version:
        diffs["version"] = f"Version changed: {m1.jarvis_version} → {m2.jarvis_version}"

    return diffs
