"""Semantic Contradiction Detector.

Uses embedding similarity for advanced contradiction detection.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from jarvis_core.contradiction.schema import (
    Claim,
    ContradictionResult,
    ContradictionType,
)


@dataclass
class SemanticConfig:
    """Configuration for semantic contradiction detection."""

    similarity_threshold: float = 0.7
    contradiction_threshold: float = 0.3
    use_negation_embedding: bool = True
    model_name: str = "all-MiniLM-L6-v2"


class SemanticContradictionDetector:
    """Semantic contradiction detector using embeddings.

    Detects contradictions by:
    1. Computing embedding similarity between claims
    2. Checking if negated version of claim A is similar to claim B
    3. Analyzing predicate-argument structure
    """

    def __init__(self, config: SemanticConfig | None = None):
        self.config = config or SemanticConfig()
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            try:
                from jarvis_core.embeddings import SentenceTransformerEmbedding

                self._embedder = SentenceTransformerEmbedding(model_name=self.config.model_name)
            except ImportError:
                # Fallback to simple embedder if sentence-transformers not available
                self._embedder = SimpleEmbedder()
        return self._embedder

    def detect(self, claim_a: Claim, claim_b: Claim) -> ContradictionResult:
        """Detect contradiction between two claims using semantic analysis."""
        # Get embeddings
        emb_a = self.embedder.embed(claim_a.text)
        emb_b = self.embedder.embed(claim_b.text)

        # Compute similarity
        similarity = self._cosine_similarity(emb_a, emb_b)

        # Check if claims are about the same topic (high similarity)
        if similarity < self.config.similarity_threshold:
            return ContradictionResult(
                claim_a=claim_a,
                claim_b=claim_b,
                is_contradictory=False,
                contradiction_type=ContradictionType.NONE,
                confidence=1 - similarity,
                scores={"semantic_similarity": similarity},
            )

        # Check negation similarity
        if self.config.use_negation_embedding:
            negated_a = self._negate_claim(claim_a.text)
            emb_neg_a = self.embedder.embed(negated_a)
            neg_similarity = self._cosine_similarity(emb_neg_a, emb_b)

            if neg_similarity > self.config.similarity_threshold:
                return ContradictionResult(
                    claim_a=claim_a,
                    claim_b=claim_b,
                    is_contradictory=True,
                    contradiction_type=ContradictionType.DIRECT,
                    confidence=neg_similarity,
                    scores={
                        "semantic_similarity": similarity,
                        "negation_similarity": neg_similarity,
                    },
                )

        # Check for partial contradiction using predicate analysis
        partial_score = self._check_partial_contradiction(claim_a, claim_b)

        if partial_score > self.config.contradiction_threshold:
            return ContradictionResult(
                claim_a=claim_a,
                claim_b=claim_b,
                is_contradictory=True,
                contradiction_type=ContradictionType.PARTIAL,
                confidence=partial_score,
                scores={
                    "semantic_similarity": similarity,
                    "partial_score": partial_score,
                },
            )

        return ContradictionResult(
            claim_a=claim_a,
            claim_b=claim_b,
            is_contradictory=False,
            contradiction_type=ContradictionType.NONE,
            confidence=1 - similarity,
            scores={"semantic_similarity": similarity},
        )

    def detect_batch(self, claims: list[Claim]) -> list[tuple[Claim, Claim, ContradictionResult]]:
        """Detect contradictions among a list of claims.

        Returns list of (claim_a, claim_b, result) tuples for contradicting pairs.
        """
        contradictions = []

        for i, claim_a in enumerate(claims):
            for claim_b in claims[i + 1 :]:
                result = self.detect(claim_a, claim_b)
                if result.is_contradictory:
                    contradictions.append((claim_a, claim_b, result))

        return contradictions

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _negate_claim(self, text: str) -> str:
        """Create negated version of claim text."""
        # Simple negation patterns
        negation_map = {
            "increases": "decreases",
            "decreases": "increases",
            "improves": "worsens",
            "worsens": "improves",
            "effective": "ineffective",
            "ineffective": "effective",
            "significant": "insignificant",
            "insignificant": "significant",
            "positive": "negative",
            "negative": "positive",
            "beneficial": "harmful",
            "harmful": "beneficial",
            "higher": "lower",
            "lower": "higher",
            "more": "less",
            "less": "more",
        }

        negated = text.lower()
        for word, neg_word in negation_map.items():
            if word in negated:
                negated = negated.replace(word, neg_word)
                break
        else:
            # Add "not" if no specific negation found
            negated = f"It is not the case that {text}"

        return negated

    def _check_partial_contradiction(self, claim_a: Claim, claim_b: Claim) -> float:
        """Check for partial contradiction based on predicate analysis."""
        text_a = claim_a.text.lower()
        text_b = claim_b.text.lower()

        # Check for opposite predicates
        opposite_predicates = [
            ("increase", "decrease"),
            ("improve", "worsen"),
            ("effective", "ineffective"),
            ("benefit", "harm"),
            ("positive", "negative"),
            ("higher", "lower"),
            ("more", "less"),
            ("significant", "insignificant"),
        ]

        for pred_a, pred_b in opposite_predicates:
            if (pred_a in text_a and pred_b in text_b) or (pred_b in text_a and pred_a in text_b):
                return 0.8

        return 0.0


class SimpleEmbedder:
    """Simple fallback embedder using bag-of-words."""

    def __init__(self):
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}

    def embed(self, text: str) -> np.ndarray:
        """Create simple TF-IDF-like embedding."""
        words = text.lower().split()

        # Simple bag-of-words embedding
        vector = np.zeros(1000)
        for word in words:
            idx = hash(word) % 1000
            vector[idx] += 1

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector


def detect_semantic_contradiction(
    claim_a: Claim,
    claim_b: Claim,
    config: SemanticConfig | None = None,
) -> ContradictionResult:
    """Convenience function for semantic contradiction detection.

    Args:
        claim_a: First claim
        claim_b: Second claim
        config: Optional configuration

    Returns:
        ContradictionResult with detection details
    """
    detector = SemanticContradictionDetector(config=config)
    return detector.detect(claim_a, claim_b)
