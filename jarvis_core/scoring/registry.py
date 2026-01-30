"""Score Normalization Registry.

Per V4-A3, this unifies all scores across modules.
All scores must be registered and normalized to 0-1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class ScoreDefinition:
    """Definition of a score metric."""

    name: str
    description: str
    direction: Literal["higher_better", "lower_better"]
    raw_min: float = 0.0
    raw_max: float = 1.0
    unit: str = ""
    calibration_note: str = ""

    def normalize(self, raw_value: float) -> float:
        """Normalize raw value to 0-1."""
        if self.raw_max == self.raw_min:
            return 0.5

        normalized = (raw_value - self.raw_min) / (self.raw_max - self.raw_min)
        normalized = max(0.0, min(1.0, normalized))

        # Flip if lower is better
        if self.direction == "lower_better":
            normalized = 1.0 - normalized

        return round(normalized, 4)


class ScoreRegistry:
    """Central registry for all score definitions."""

    _instance: ScoreRegistry | None = None
    _definitions: dict[str, ScoreDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._definitions = {}
            cls._instance._register_defaults()
        return cls._instance

    def _register_defaults(self):
        """Register all default scores."""
        # Research metrics
        self.register(
            ScoreDefinition(
                name="roi_score",
                description="Research return on investment",
                direction="higher_better",
                calibration_note="Based on output value / time invested",
            )
        )
        self.register(
            ScoreDefinition(
                name="gap_score",
                description="Research gap opportunity",
                direction="higher_better",
                calibration_note="Higher = less explored area",
            )
        )
        self.register(
            ScoreDefinition(
                name="novelty",
                description="Novelty of research",
                direction="higher_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="impact",
                description="Future impact potential",
                direction="higher_better",
            )
        )

        # Feasibility metrics
        self.register(
            ScoreDefinition(
                name="difficulty",
                description="Experiment difficulty",
                direction="lower_better",
                calibration_note="0=easy, 1=hard",
            )
        )
        self.register(
            ScoreDefinition(
                name="cost",
                description="Experiment cost",
                direction="lower_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="reproducibility",
                description="Reproducibility likelihood",
                direction="higher_better",
            )
        )

        # Risk metrics
        self.register(
            ScoreDefinition(
                name="burnout_risk",
                description="Burnout risk level",
                direction="lower_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="collapse_risk",
                description="Field collapse risk",
                direction="lower_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="culture_risk_index",
                description="Lab culture risk",
                direction="lower_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="stop_score",
                description="Theme termination score",
                direction="lower_better",
                calibration_note="Higher = more reason to stop",
            )
        )

        # Grant/Career metrics
        self.register(
            ScoreDefinition(
                name="grant_score",
                description="Grant success probability",
                direction="higher_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="alignment",
                description="Alignment with target",
                direction="higher_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="competitiveness_score",
                description="Career competitiveness",
                direction="higher_better",
            )
        )

        # Confidence metrics
        self.register(
            ScoreDefinition(
                name="confidence_index",
                description="Claim confidence",
                direction="higher_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="citation_strength",
                description="Citation power index",
                direction="higher_better",
            )
        )
        self.register(
            ScoreDefinition(
                name="survival_probability",
                description="Paper longevity probability",
                direction="higher_better",
            )
        )

    def register(self, definition: ScoreDefinition) -> None:
        """Register a score definition."""
        self._definitions[definition.name] = definition

    def get(self, name: str) -> ScoreDefinition | None:
        """Get score definition by name."""
        return self._definitions.get(name)

    def normalize(self, name: str, raw_value: float) -> float:
        """Normalize a score value.

        Args:
            name: Score name.
            raw_value: Raw score value.

        Returns:
            Normalized 0-1 value.

        Raises:
            ValueError: If score is not registered.
        """
        definition = self._definitions.get(name)
        if not definition:
            raise ValueError(f"Score '{name}' not registered. Register before use.")
        return definition.normalize(raw_value)

    def is_registered(self, name: str) -> bool:
        """Check if score is registered."""
        return name in self._definitions

    def list_scores(self) -> list[str]:
        """List all registered scores."""
        return list(self._definitions.keys())


# Singleton instance
_registry = ScoreRegistry()


def normalize_score(name: str, raw_value: float) -> float:
    """Normalize a score value using the global registry."""
    return _registry.normalize(name, raw_value)


def get_score_info(name: str) -> ScoreDefinition | None:
    """Get score definition from global registry."""
    return _registry.get(name)


def register_score(definition: ScoreDefinition) -> None:
    """Register a new score in the global registry."""
    _registry.register(definition)


def validate_score_names(scores: dict[str, float]) -> list[str]:
    """Validate that all score names are registered.

    Returns list of unregistered names.
    """
    return [name for name in scores if not _registry.is_registered(name)]