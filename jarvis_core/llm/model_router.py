"""Model Router.

Per RP-174, routes tasks to appropriate models.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Callable
from enum import Enum


class TaskType(Enum):
    """Task types for model routing."""

    EXTRACT = "extract"
    GENERATE = "generate"
    SUMMARIZE = "summarize"
    CLASSIFY = "classify"
    JUDGE = "judge"


class ModelProvider(Enum):
    """Model providers."""

    GEMINI = "gemini"
    OLLAMA = "ollama"
    OPENAI = "openai"
    RULE = "rule"  # Rule-based (no LLM)


@dataclass
class ModelConfig:
    """Configuration for a model."""

    provider: ModelProvider
    model_name: str
    max_tokens: int = 1000
    temperature: float = 0.0
    timeout_seconds: float = 30.0


@dataclass
class RoutingDecision:
    """Result of model routing."""

    task_type: TaskType
    model_config: ModelConfig
    reason: str
    fallback: Optional[ModelConfig] = None


# Default model configurations
DEFAULT_MODELS = {
    ModelProvider.GEMINI: ModelConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-1.5-flash",
        max_tokens=2000,
    ),
    ModelProvider.OLLAMA: ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_name="llama3",
        max_tokens=1000,
    ),
    ModelProvider.RULE: ModelConfig(
        provider=ModelProvider.RULE,
        model_name="rule_based",
        max_tokens=0,
    ),
}


class ModelRouter:
    """Routes tasks to appropriate models."""

    def __init__(
        self,
        primary_provider: ModelProvider = ModelProvider.GEMINI,
        fallback_provider: ModelProvider = ModelProvider.RULE,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self._availability: dict = {}

    def check_availability(self, provider: ModelProvider) -> bool:
        """Check if a provider is available."""
        if provider == ModelProvider.RULE:
            return True

        if provider == ModelProvider.GEMINI:
            import os
            return bool(os.environ.get("GOOGLE_API_KEY"))

        if provider == ModelProvider.OLLAMA:
            # Check if ollama is running
            try:
                import requests
                resp = requests.get("http://localhost:11434/api/tags", timeout=2)
                return resp.status_code == 200
            except Exception:
                return False

        return False

    def route(
        self,
        task_type: TaskType,
        complexity: str = "low",
        budget_tokens: Optional[int] = None,
    ) -> RoutingDecision:
        """Route a task to appropriate model.

        Args:
            task_type: Type of task.
            complexity: low, medium, high.
            budget_tokens: Token budget constraint.

        Returns:
            RoutingDecision with selected model.
        """
        # Check primary availability
        primary_available = self.check_availability(self.primary_provider)

        # Simple tasks can use rules
        if task_type == TaskType.CLASSIFY and complexity == "low":
            return RoutingDecision(
                task_type=task_type,
                model_config=DEFAULT_MODELS[ModelProvider.RULE],
                reason="Simple classification uses rule-based",
            )

        # Use primary if available
        if primary_available:
            config = DEFAULT_MODELS.get(
                self.primary_provider,
                DEFAULT_MODELS[ModelProvider.GEMINI],
            )
            if budget_tokens:
                config = ModelConfig(
                    provider=config.provider,
                    model_name=config.model_name,
                    max_tokens=min(config.max_tokens, budget_tokens),
                    temperature=config.temperature,
                )

            fallback = DEFAULT_MODELS.get(self.fallback_provider)

            return RoutingDecision(
                task_type=task_type,
                model_config=config,
                reason=f"Primary provider {self.primary_provider.value} available",
                fallback=fallback,
            )

        # Fallback
        return RoutingDecision(
            task_type=task_type,
            model_config=DEFAULT_MODELS[self.fallback_provider],
            reason=f"Fallback to {self.fallback_provider.value}",
        )


# Global router
_router: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    """Get global model router."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def route_task(task_type: TaskType) -> RoutingDecision:
    """Route a task using global router."""
    return get_router().route(task_type)
