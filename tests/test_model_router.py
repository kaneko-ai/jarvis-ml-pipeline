"""Tests for llm.model_router module."""

from unittest.mock import patch

from jarvis_core.llm.model_router import (
    TaskType,
    ModelProvider,
    ModelConfig,
    RoutingDecision,
    ModelRouter,
    get_router,
    route_task,
    DEFAULT_MODELS,
    LOCAL_FIRST_CHAIN,
)


class TestTaskType:
    def test_values(self):
        # Enum comparison with .value
        assert TaskType.EXTRACT.value == "extract"
        assert TaskType.GENERATE.value == "generate"
        assert TaskType.SUMMARIZE.value == "summarize"
        assert TaskType.CLASSIFY.value == "classify"
        assert TaskType.JUDGE.value == "judge"
        assert TaskType.CHAT.value == "chat"
        assert TaskType.EMBED.value == "embed"


class TestModelProvider:
    def test_values(self):
        # Enum comparison with .value
        assert ModelProvider.GEMINI.value == "gemini"
        assert ModelProvider.OLLAMA.value == "ollama"
        assert ModelProvider.LLAMACPP.value == "llamacpp"
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.RULE.value == "rule"


class TestModelConfig:
    def test_creation(self):
        config = ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name="llama3.2",
            max_tokens=2000,
        )

        assert config.provider == ModelProvider.OLLAMA
        assert config.model_name == "llama3.2"

    def test_defaults(self):
        config = ModelConfig(
            provider=ModelProvider.GEMINI,
            model_name="gemini-flash",
        )

        assert config.max_tokens == 1000
        assert config.temperature == 0.0


class TestRoutingDecision:
    def test_creation(self):
        config = ModelConfig(provider=ModelProvider.OLLAMA, model_name="test")
        decision = RoutingDecision(
            task_type=TaskType.GENERATE,
            model_config=config,
            reason="Test routing",
        )

        assert decision.task_type == TaskType.GENERATE
        assert decision.fallback is None


class TestDefaultModels:
    def test_has_providers(self):
        assert ModelProvider.GEMINI in DEFAULT_MODELS
        assert ModelProvider.OLLAMA in DEFAULT_MODELS
        assert ModelProvider.RULE in DEFAULT_MODELS


class TestLocalFirstChain:
    def test_order(self):
        # Ollama should be first
        assert LOCAL_FIRST_CHAIN[0] == ModelProvider.OLLAMA
        # Rule should be last (guaranteed fallback)
        assert LOCAL_FIRST_CHAIN[-1] == ModelProvider.RULE


class TestModelRouter:
    def test_init_default(self):
        router = ModelRouter()

        assert router.primary_provider == ModelProvider.OLLAMA
        assert router.local_first is True

    def test_init_custom(self):
        router = ModelRouter(
            primary_provider=ModelProvider.GEMINI,
            local_first=False,
        )

        assert router.primary_provider == ModelProvider.GEMINI

    def test_check_availability_rule(self):
        router = ModelRouter()

        # Rule provider is always available
        result = router.check_availability(ModelProvider.RULE)

        assert result is True

    def test_find_available_provider(self):
        router = ModelRouter()

        with patch.object(router, "check_availability") as mock_check:
            mock_check.side_effect = lambda p: p == ModelProvider.RULE

            provider = router.find_available_provider()

            # Should fall back to RULE
            assert provider == ModelProvider.RULE

    def test_route_simple(self):
        router = ModelRouter()

        with patch.object(router, "find_available_provider", return_value=ModelProvider.RULE):
            decision = router.route(TaskType.CLASSIFY)

            assert decision.task_type == TaskType.CLASSIFY

    def test_route_with_complexity(self):
        router = ModelRouter()

        with patch.object(router, "find_available_provider", return_value=ModelProvider.RULE):
            decision = router.route(TaskType.GENERATE, complexity="high")

            assert decision is not None


class TestGetRouter:
    def test_returns_router(self):
        router = get_router()

        assert isinstance(router, ModelRouter)


class TestRouteTask:
    def test_routes_task(self):
        decision = route_task(TaskType.SUMMARIZE)

        assert decision.task_type == TaskType.SUMMARIZE
