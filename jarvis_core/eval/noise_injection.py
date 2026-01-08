"""Negative Sampling for Noise Testing.

Per RP-122, injects noise to test retrieval robustness.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class NoiseConfig:
    """Configuration for noise injection."""

    noise_ratio: float = 0.2  # Ratio of noise documents
    seed: int = 42
    noise_sources: list[str] = None  # Pool of noise texts

    def __post_init__(self):
        if self.noise_sources is None:
            self.noise_sources = DEFAULT_NOISE_TEXTS


# Default noise texts (unrelated to immunology)
DEFAULT_NOISE_TEXTS = [
    "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet.",
    "Climate change affects global weather patterns and sea levels worldwide.",
    "The history of computing began with early mechanical calculators.",
    "Quantum mechanics describes behavior of matter at atomic scales.",
    "Economic theories explain market behavior and resource allocation.",
    "Renaissance art featured perspective and human anatomy studies.",
    "Photosynthesis converts sunlight into chemical energy in plants.",
    "Plate tectonics explains continental drift and earthquake patterns.",
    "The industrial revolution transformed manufacturing and society.",
    "Machine learning algorithms improve with more training data.",
]


@dataclass
class NoisyRetrievalResult:
    """Result with noise injection details."""

    original_docs: list[str]
    noise_docs: list[str]
    combined_docs: list[str]
    noise_indices: list[int]


def inject_noise(
    documents: list[str],
    config: NoiseConfig | None = None,
) -> NoisyRetrievalResult:
    """Inject noise documents into retrieval results.

    Args:
        documents: Original retrieved documents.
        config: Noise configuration.

    Returns:
        NoisyRetrievalResult with noise injected.
    """
    if config is None:
        config = NoiseConfig()

    # Seed for reproducibility
    rng = random.Random(config.seed)

    # Calculate number of noise docs
    num_noise = max(1, int(len(documents) * config.noise_ratio))

    # Select noise texts
    noise_docs = rng.sample(
        config.noise_sources,
        min(num_noise, len(config.noise_sources)),
    )

    # Combine and shuffle
    combined = documents + noise_docs
    noise_indices = list(range(len(documents), len(combined)))

    # Shuffle while tracking noise positions
    indices = list(range(len(combined)))
    rng.shuffle(indices)

    shuffled = [combined[i] for i in indices]
    new_noise_indices = [
        shuffled_idx for shuffled_idx, orig_idx in enumerate(indices) if orig_idx >= len(documents)
    ]

    return NoisyRetrievalResult(
        original_docs=documents,
        noise_docs=noise_docs,
        combined_docs=shuffled,
        noise_indices=new_noise_indices,
    )


def evaluate_noise_robustness(
    clean_claims: list[str],
    noisy_claims: list[str],
) -> dict:
    """Evaluate robustness to noise.

    Compares claims generated with and without noise.

    Args:
        clean_claims: Claims from clean retrieval.
        noisy_claims: Claims from noisy retrieval.

    Returns:
        Dict with robustness metrics.
    """
    clean_set = set(c.lower().strip() for c in clean_claims)
    noisy_set = set(c.lower().strip() for c in noisy_claims)

    # Claims preserved despite noise
    preserved = clean_set & noisy_set

    # Claims lost due to noise
    lost = clean_set - noisy_set

    # New claims (possibly hallucinated from noise)
    added = noisy_set - clean_set

    preservation_rate = len(preserved) / len(clean_set) if clean_set else 1.0
    hallucination_rate = len(added) / len(noisy_set) if noisy_set else 0.0

    return {
        "preservation_rate": preservation_rate,
        "hallucination_rate": hallucination_rate,
        "claims_preserved": len(preserved),
        "claims_lost": len(lost),
        "claims_added": len(added),
        "robust": preservation_rate >= 0.8 and hallucination_rate <= 0.2,
    }
