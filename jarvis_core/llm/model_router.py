"""Model Router.

Per RP-174, routes tasks to appropriate models.
Extended for Local-First architecture with fallback chain.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task types for model routing."""

    EXTRACT = "extract"
    GENERATE = "generate"
    SUMMARIZE = "summarize"
    CLASSIFY = "classify"
    JUDGE = "judge"
    CHAT = "chat"
    EMBED = "embed"


class ModelProvider(Enum):
    """Model providers."""

    GEMINI = "gemini"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    OPENAI = "openai"
    RULE = "rule"  # Rule-based (no LLM)


@dataclass
class ModelConfig:
    """Configuration for a model."""

    provider: ModelProvider
    model_name: str
    max_tokens: int = 1000
    temperature: float = 0.0
    timeout_seconds: float = 120.0


@dataclass
class RoutingDecision:
    """Result of model routing."""

    task_type: TaskType
    model_config: ModelConfig
    reason: str
    fallback: ModelConfig | None = None


# Default model configurations
DEFAULT_MODELS = {
    ModelProvider.GEMINI: ModelConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-2.0-flash",
        max_tokens=2000,
    ),
    ModelProvider.OLLAMA: ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_name="llama3.2",
        max_tokens=1000,
    ),
    ModelProvider.LLAMACPP: ModelConfig(
        provider=ModelProvider.LLAMACPP,
        model_name="local-gguf",
        max_tokens=512,
    ),
    ModelProvider.RULE: ModelConfig(
        provider=ModelProvider.RULE,
        model_name="rule_based",
        max_tokens=0,
    ),
}

# Local-First fallback chain
LOCAL_FIRST_CHAIN = [
    ModelProvider.OLLAMA,
    ModelProvider.LLAMACPP,
    ModelProvider.GEMINI,
    ModelProvider.RULE,
]


class ModelRouter:
    """Routes tasks to appropriate models.

    Supports Local-First architecture with automatic fallback.
    """

    def __init__(
        self,
        primary_provider: ModelProvider = ModelProvider.OLLAMA,
        fallback_chain: list[ModelProvider] | None = None,
        local_first: bool = True,
    ):
        self.primary_provider = primary_provider
        self.fallback_chain = fallback_chain or LOCAL_FIRST_CHAIN
        self.local_first = local_first
        self._availability_cache: dict = {}
        self._adapters: dict = {}

    def check_availability(self, provider: ModelProvider) -> bool:
        """Check if a provider is available."""
        if provider in self._availability_cache:
            return self._availability_cache[provider]

        available = self._check_provider(provider)
        self._availability_cache[provider] = available
        return available

    def _check_provider(self, provider: ModelProvider) -> bool:
        """Actually check provider availability."""
        if provider == ModelProvider.RULE:
            return True

        if provider == ModelProvider.GEMINI:
            return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))

        if provider == ModelProvider.OLLAMA:
            try:
                from jarvis_core.llm.ollama_adapter import OllamaAdapter

                adapter = OllamaAdapter()
                return adapter.is_available()
            except Exception as e:
                logger.debug(f"Ollama not available: {e}")
                return False

        if provider == ModelProvider.LLAMACPP:
            try:
                from jarvis_core.llm.llamacpp_adapter import LlamaCppAdapter

                adapter = LlamaCppAdapter()
                return adapter.is_available() and adapter.config.model_path is not None
            except Exception as e:
                logger.debug(f"llama.cpp not available: {e}")
                return False

        return False

    def get_adapter(self, provider: ModelProvider):
        """Get or create adapter for provider."""
        if provider in self._adapters:
            return self._adapters[provider]

        if provider == ModelProvider.OLLAMA:
            from jarvis_core.llm.ollama_adapter import OllamaAdapter

            self._adapters[provider] = OllamaAdapter()
        elif provider == ModelProvider.LLAMACPP:
            from jarvis_core.llm.llamacpp_adapter import LlamaCppAdapter

            self._adapters[provider] = LlamaCppAdapter()
        else:
            return None

        return self._adapters[provider]

    def find_available_provider(self) -> ModelProvider | None:
        """Find first available provider from fallback chain."""
        for provider in self.fallback_chain:
            if self.check_availability(provider):
                logger.info(f"Using provider: {provider.value}")
                return provider
        return None

    def route(
        self,
        task_type: TaskType,
        complexity: str = "low",
        budget_tokens: int | None = None,
        prefer_local: bool = True,
    ) -> RoutingDecision:
        """Route a task to appropriate model.

        Args:
            task_type: Type of task.
            complexity: low, medium, high.
            budget_tokens: Token budget constraint.
            prefer_local: Prefer local providers.

        Returns:
            RoutingDecision with selected model.
        """
        # Simple tasks can use rules
        if task_type == TaskType.CLASSIFY and complexity == "low":
            return RoutingDecision(
                task_type=task_type,
                model_config=DEFAULT_MODELS[ModelProvider.RULE],
                reason="Simple classification uses rule-based",
            )

        # Local-first: find available local provider
        if self.local_first or prefer_local:
            provider = self.find_available_provider()
            if provider:
                config = DEFAULT_MODELS.get(
                    provider,
                    DEFAULT_MODELS[ModelProvider.RULE],
                )
                if budget_tokens:
                    config = ModelConfig(
                        provider=config.provider,
                        model_name=config.model_name,
                        max_tokens=min(config.max_tokens, budget_tokens),
                        temperature=config.temperature,
                    )

                # Find fallback
                fallback = None
                for p in self.fallback_chain:
                    if p != provider and self.check_availability(p):
                        fallback = DEFAULT_MODELS.get(p)
                        break

                return RoutingDecision(
                    task_type=task_type,
                    model_config=config,
                    reason=f"Local-first: using {provider.value}",
                    fallback=fallback,
                )

        # Fallback to rule-based
        return RoutingDecision(
            task_type=task_type,
            model_config=DEFAULT_MODELS[ModelProvider.RULE],
            reason="No provider available, using rule-based",
        )

    def generate(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, **kwargs
    ) -> str:
        """Generate text using best available provider."""
        decision = self.route(TaskType.GENERATE)
        adapter = self.get_adapter(decision.model_config.provider)

        if adapter is None:
            raise RuntimeError(f"No adapter for {decision.model_config.provider}")

        return adapter.generate(prompt, max_tokens=max_tokens, temperature=temperature, **kwargs)

    def chat(
        self, messages: list[dict], max_tokens: int = 1024, temperature: float = 0.7, **kwargs
    ) -> str:
        """Chat using best available provider."""
        decision = self.route(TaskType.CHAT)
        adapter = self.get_adapter(decision.model_config.provider)

        if adapter is None:
            raise RuntimeError(f"No adapter for {decision.model_config.provider}")

        return adapter.chat(messages, max_tokens=max_tokens, temperature=temperature, **kwargs)

    def generate_stream(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, **kwargs
    ) -> Generator[str, None, None]:
        """Streaming generation."""
        decision = self.route(TaskType.GENERATE)
        adapter = self.get_adapter(decision.model_config.provider)

        if adapter is None:
            raise RuntimeError(f"No adapter for {decision.model_config.provider}")

        if hasattr(adapter, "generate_stream"):
            yield from adapter.generate_stream(
                prompt, max_tokens=max_tokens, temperature=temperature, **kwargs
            )
        else:
            # Fallback to non-streaming
            yield adapter.generate(prompt, max_tokens=max_tokens, temperature=temperature, **kwargs)


# Global router
_router: ModelRouter | None = None


def get_router(local_first: bool = True) -> ModelRouter:
    """Get global model router."""
    global _router
    if _router is None:
        _router = ModelRouter(local_first=local_first)
    return _router


def route_task(task_type: TaskType) -> RoutingDecision:
    """Route a task using global router."""
    return get_router().route(task_type)