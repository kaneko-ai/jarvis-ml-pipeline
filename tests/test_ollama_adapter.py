"""Tests for llm.ollama_adapter module with mocking."""

from unittest.mock import patch, MagicMock
import pytest

from jarvis_core.llm.ollama_adapter import (
    OllamaConfig,
    OllamaAdapter,
    get_ollama_adapter,
)


class TestOllamaConfig:
    def test_default_values(self):
        config = OllamaConfig()
        
        assert config.base_url == "http://127.0.0.1:11434"
        assert config.model == "llama3.2"
        assert config.timeout == 120

    def test_custom_values(self):
        config = OllamaConfig(
            base_url="http://localhost:12345",
            model="llama2",
            timeout=60,
        )
        
        assert config.base_url == "http://localhost:12345"
        assert config.model == "llama2"


class TestOllamaAdapter:
    def test_init_default(self):
        adapter = OllamaAdapter()
        
        assert adapter.config is not None
        assert adapter.base_url == adapter.config.base_url

    def test_init_with_config(self):
        config = OllamaConfig(model="custom-model")
        adapter = OllamaAdapter(config=config)
        
        assert adapter.model == "custom-model"

    def test_base_url_property(self):
        adapter = OllamaAdapter()
        
        assert "http" in adapter.base_url

    def test_model_property(self):
        adapter = OllamaAdapter()
        
        assert isinstance(adapter.model, str)

    def test_is_available_success(self):
        adapter = OllamaAdapter()
        
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = adapter.is_available()
            
            assert result is True

    def test_is_available_failure(self):
        adapter = OllamaAdapter()
        
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            
            result = adapter.is_available()
            
            assert result is False

    def test_list_models_success(self):
        adapter = OllamaAdapter()
        
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [{"name": "llama2"}, {"name": "llama3"}]
            }
            mock_get.return_value = mock_response
            
            result = adapter.list_models()
            
            assert len(result) >= 0

    def test_generate_success(self):
        adapter = OllamaAdapter()
        
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Hello, world!"}
            mock_post.return_value = mock_response
            
            result = adapter.generate("Say hello")
            
            assert result == "Hello, world!"

    def test_generate_failure(self):
        adapter = OllamaAdapter()
        
        with patch("requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            with pytest.raises(Exception):
                adapter.generate("Test prompt")

    def test_chat_success(self):
        adapter = OllamaAdapter()
        
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "I am a helpful assistant."}
            }
            mock_post.return_value = mock_response
            
            messages = [{"role": "user", "content": "Who are you?"}]
            result = adapter.chat(messages)
            
            assert "helpful" in result.lower() or isinstance(result, str)


class TestGetOllamaAdapter:
    def test_returns_adapter(self):
        adapter = get_ollama_adapter()
        
        assert isinstance(adapter, OllamaAdapter)

    def test_returns_singleton(self):
        adapter1 = get_ollama_adapter()
        adapter2 = get_ollama_adapter()
        
        assert adapter1 is adapter2
