"""Cache Key Contract.

Per V4.2 Sprint 2, this defines deterministic cache key computation.
Key includes: input_hash, extractor_version, model_version, thresholds, config_hash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


@dataclass
class CacheKeyContract:
    """Contract for cache key components."""

    input_hash: str
    extractor_version: str = "1.0"
    model_version: str = ""
    thresholds: dict[str, float] = field(default_factory=dict)
    config_hash: str = ""
    stage: str = ""

    def compute_key(self) -> str:
        """Compute deterministic cache key.

        Returns:
            SHA-256 hash of all components.
        """
        components = [
            f"input:{self.input_hash}",
            f"extractor:{self.extractor_version}",
            f"model:{self.model_version}",
            f"thresholds:{json.dumps(self.thresholds, sort_keys=True)}",
            f"config:{self.config_hash}",
            f"stage:{self.stage}",
        ]

        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "input_hash": self.input_hash,
            "extractor_version": self.extractor_version,
            "model_version": self.model_version,
            "thresholds": self.thresholds,
            "config_hash": self.config_hash,
            "stage": self.stage,
            "computed_key": self.compute_key(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CacheKeyContract:
        return cls(
            input_hash=data["input_hash"],
            extractor_version=data.get("extractor_version", "1.0"),
            model_version=data.get("model_version", ""),
            thresholds=data.get("thresholds", {}),
            config_hash=data.get("config_hash", ""),
            stage=data.get("stage", ""),
        )


def compute_cache_key(
    input_hash: str,
    stage: str = "",
    extractor_version: str = "1.0",
    model_version: str = "",
    thresholds: dict[str, float] = None,
    config_hash: str = "",
) -> str:
    """Compute cache key from components.

    Args:
        input_hash: Hash of input content.
        stage: Processing stage.
        extractor_version: Extractor/parser version.
        model_version: LLM model version.
        thresholds: Scoring thresholds.
        config_hash: Configuration hash.

    Returns:
        Deterministic cache key.
    """
    contract = CacheKeyContract(
        input_hash=input_hash,
        extractor_version=extractor_version,
        model_version=model_version,
        thresholds=thresholds or {},
        config_hash=config_hash,
        stage=stage,
    )
    return contract.compute_key()


def validate_key_match(
    key1: CacheKeyContract,
    key2: CacheKeyContract,
) -> tuple[bool, list]:
    """Validate if two keys should match.

    Args:
        key1: First key contract.
        key2: Second key contract.

    Returns:
        Tuple of (matches, list of differences).
    """
    differences = []

    if key1.input_hash != key2.input_hash:
        differences.append(f"input_hash: {key1.input_hash[:8]} vs {key2.input_hash[:8]}")

    if key1.extractor_version != key2.extractor_version:
        differences.append(f"extractor: {key1.extractor_version} vs {key2.extractor_version}")

    if key1.model_version != key2.model_version:
        differences.append(f"model: {key1.model_version} vs {key2.model_version}")

    if key1.thresholds != key2.thresholds:
        differences.append("thresholds differ")

    if key1.config_hash != key2.config_hash:
        differences.append(f"config: {key1.config_hash[:8]} vs {key2.config_hash[:8]}")

    return len(differences) == 0, differences