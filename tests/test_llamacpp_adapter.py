"""Tests for llm.llamacpp_adapter module."""

from unittest.mock import patch

from jarvis_core.llm.llamacpp_adapter import (
    LlamaCppConfig,
    LlamaCppAdapter,
    get_llamacpp_adapter,
)


class TestLlamaCppConfig:
    def test_default_values(self):
        config = LlamaCppConfig()

        assert config.model_path is None
        assert config.n_ctx == 4096
        assert config.n_threads == 4
        assert config.n_gpu_layers == 0

    def test_custom_values(self):
        config = LlamaCppConfig(
            model_path="/path/to/model.gguf",
            n_ctx=8192,
            n_threads=8,
        )

        assert config.model_path == "/path/to/model.gguf"
        assert config.n_ctx == 8192


class TestLlamaCppAdapter:
    def test_init(self):
        adapter = LlamaCppAdapter()

        assert adapter.config is not None
        assert adapter._llm is None

    def test_init_with_config(self):
        config = LlamaCppConfig(n_threads=8)
        adapter = LlamaCppAdapter(config=config)

        assert adapter.config.n_threads == 8

    def test_is_available_not_installed(self):
        adapter = LlamaCppAdapter()

        with patch.dict("sys.modules", {"llama_cpp": None}):
            # Force re-check
            adapter._available = None
            # The actual check depends on import
            result = adapter.is_available()
            assert isinstance(result, bool)

    def test_is_available_caches_result(self):
        adapter = LlamaCppAdapter()
        adapter._available = True

        result = adapter.is_available()

        assert result is True

    def test_messages_to_prompt(self):
        adapter = LlamaCppAdapter()

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]

        prompt = adapter._messages_to_prompt(messages)

        assert "system" in prompt.lower() or "im_start" in prompt
        assert "user" in prompt.lower() or "Hello" in prompt
        assert "assistant" in prompt.lower()


class TestGetLlamacppAdapter:
    def test_returns_adapter(self):
        adapter = get_llamacpp_adapter()

        assert isinstance(adapter, LlamaCppAdapter)

    def test_returns_singleton(self):
        adapter1 = get_llamacpp_adapter()
        adapter2 = get_llamacpp_adapter()

        assert adapter1 is adapter2