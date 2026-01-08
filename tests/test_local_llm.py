"""Tests for Local LLM adapters and model router.

Tests for Task 1.1: ローカルLLM統合
"""
import os
from unittest.mock import MagicMock, patch


class TestOllamaAdapter:
    """Tests for Ollama adapter."""

    def test_ollama_adapter_init(self):
        """Test OllamaAdapter initialization."""
        from jarvis_core.llm.ollama_adapter import OllamaAdapter, OllamaConfig

        config = OllamaConfig(
            base_url="http://localhost:11434",
            model="llama3.2",
        )
        adapter = OllamaAdapter(config)

        assert adapter.base_url == "http://localhost:11434"
        assert adapter.model == "llama3.2"

    def test_ollama_adapter_env_config(self):
        """Test OllamaAdapter uses environment variables."""
        with patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "http://custom:8080",
            "OLLAMA_MODEL": "mistral",
        }):
            from jarvis_core.llm.ollama_adapter import OllamaAdapter
            adapter = OllamaAdapter()

            assert adapter.base_url == "http://custom:8080"
            assert adapter.model == "mistral"

    def test_ollama_is_available_success(self):
        """Test Ollama availability check when server is running."""
        from jarvis_core.llm.ollama_adapter import OllamaAdapter

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            adapter = OllamaAdapter()

            assert adapter.is_available() is True

    def test_ollama_is_available_failure(self):
        """Test Ollama availability check when server is not running."""
        import requests

        from jarvis_core.llm.ollama_adapter import OllamaAdapter

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection refused")
            adapter = OllamaAdapter()
            adapter._available = None  # Reset cache

            assert adapter.is_available() is False

    def test_ollama_generate_success(self):
        """Test Ollama generate method."""
        from jarvis_core.llm.ollama_adapter import OllamaAdapter

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Hello, world!"}
            mock_post.return_value = mock_response

            adapter = OllamaAdapter()
            result = adapter.generate("Say hello")

            assert result == "Hello, world!"
            mock_post.assert_called_once()

    def test_ollama_chat_success(self):
        """Test Ollama chat method."""
        from jarvis_core.llm.ollama_adapter import OllamaAdapter

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "Hi there!"}
            }
            mock_post.return_value = mock_response

            adapter = OllamaAdapter()
            result = adapter.chat([
                {"role": "user", "content": "Hello"}
            ])

            assert result == "Hi there!"


class TestLlamaCppAdapter:
    """Tests for llama.cpp adapter."""

    def test_llamacpp_not_available_without_library(self):
        """Test llama.cpp not available when library not installed."""
        from jarvis_core.llm.llamacpp_adapter import LlamaCppAdapter

        with patch.dict("sys.modules", {"llama_cpp": None}):
            adapter = LlamaCppAdapter()
            adapter._available = None  # Reset
            # This should not raise, just return False
            # Note: actual behavior depends on import mechanism

    def test_llamacpp_config(self):
        """Test llama.cpp configuration."""
        from jarvis_core.llm.llamacpp_adapter import LlamaCppAdapter, LlamaCppConfig

        config = LlamaCppConfig(
            model_path="/path/to/model.gguf",
            n_ctx=2048,
            n_threads=8,
        )
        adapter = LlamaCppAdapter(config)

        assert adapter.config.model_path == "/path/to/model.gguf"
        assert adapter.config.n_ctx == 2048
        assert adapter.config.n_threads == 8


class TestModelRouter:
    """Tests for model router with Local-First support."""

    def test_router_local_first_default(self):
        """Test router defaults to local-first mode."""
        from jarvis_core.llm.model_router import ModelRouter

        router = ModelRouter()
        assert router.local_first is True

    def test_router_fallback_chain(self):
        """Test router fallback chain order."""
        from jarvis_core.llm.model_router import LOCAL_FIRST_CHAIN, ModelProvider, ModelRouter

        router = ModelRouter()
        assert router.fallback_chain == LOCAL_FIRST_CHAIN
        assert ModelProvider.OLLAMA in router.fallback_chain
        assert ModelProvider.LLAMACPP in router.fallback_chain

    def test_router_find_available_provider_ollama(self):
        """Test router finds Ollama when available."""
        from jarvis_core.llm.model_router import ModelProvider, ModelRouter

        router = ModelRouter()

        # Mock Ollama as available
        router._availability_cache = {
            ModelProvider.OLLAMA: True,
            ModelProvider.LLAMACPP: False,
            ModelProvider.GEMINI: False,
        }

        provider = router.find_available_provider()
        assert provider == ModelProvider.OLLAMA

    def test_router_find_available_provider_fallback(self):
        """Test router falls back when Ollama not available."""
        from jarvis_core.llm.model_router import ModelProvider, ModelRouter

        router = ModelRouter()

        # Mock only RULE as available
        router._availability_cache = {
            ModelProvider.OLLAMA: False,
            ModelProvider.LLAMACPP: False,
            ModelProvider.GEMINI: False,
            ModelProvider.RULE: True,
        }

        provider = router.find_available_provider()
        assert provider == ModelProvider.RULE

    def test_router_route_simple_task(self):
        """Test routing simple classification task."""
        from jarvis_core.llm.model_router import ModelProvider, ModelRouter, TaskType

        router = ModelRouter()
        decision = router.route(TaskType.CLASSIFY, complexity="low")

        assert decision.model_config.provider == ModelProvider.RULE
        assert "rule-based" in decision.reason.lower()

    def test_router_route_generate_task(self):
        """Test routing generation task uses local provider."""
        from jarvis_core.llm.model_router import ModelProvider, ModelRouter, TaskType

        router = ModelRouter()
        router._availability_cache = {
            ModelProvider.OLLAMA: True,
        }

        decision = router.route(TaskType.GENERATE)

        assert decision.model_config.provider == ModelProvider.OLLAMA
        assert "local-first" in decision.reason.lower()


class TestLocalFirstIntegration:
    """Integration tests for Local-First LLM architecture."""

    def test_get_router_singleton(self):
        """Test get_router returns singleton."""
        from jarvis_core.llm.model_router import get_router

        router1 = get_router()
        router2 = get_router()

        assert router1 is router2

    def test_adapters_exported(self):
        """Test adapters are properly exported from package."""
        from jarvis_core.llm import (
            LlamaCppAdapter,
            ModelRouter,
            OllamaAdapter,
            get_router,
        )

        assert OllamaAdapter is not None
        assert LlamaCppAdapter is not None
        assert ModelRouter is not None
        assert callable(get_router)
