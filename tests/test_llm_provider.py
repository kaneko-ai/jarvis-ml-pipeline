"""Unit tests for LLM provider switching."""
from pathlib import Path
import sys
import types
from unittest.mock import MagicMock, patch
import os

# Stub google modules before importing LLM
google_stub = types.ModuleType("google")
google_genai_stub = types.ModuleType("google.genai")


class _DummyErrors:
    class ServerError(Exception):
        ...

    class ClientError(Exception):
        ...


class _DummyClient:
    def __init__(self, api_key=None):
        self.models = MagicMock()


google_genai_stub.errors = _DummyErrors
google_genai_stub.Client = _DummyClient
google_stub.genai = google_genai_stub
sys.modules["google"] = google_stub
sys.modules["google.genai"] = google_genai_stub

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.llm_utils import LLMClient, Message  # noqa: E402


class TestOllamaProvider:
    """Tests for Ollama provider."""

    def test_ollama_client_init(self):
        """Test Ollama client initialization."""
        client = LLMClient(model="llama3.2", provider="ollama")
        assert client.provider == "ollama"
        assert client.model == "llama3.2"

    def test_ollama_chat_success(self):
        """Test successful Ollama chat call."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "Hello from Ollama!"}
            }
            mock_post.return_value = mock_response

            client = LLMClient(model="llama3.2", provider="ollama")
            result = client.chat([Message(role="user", content="Hello")])

            assert result == "Hello from Ollama!"
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/api/chat" in call_args[0][0]
            assert call_args[1]["json"]["model"] == "llama3.2"
            assert call_args[1]["json"]["stream"] is False

    def test_ollama_chat_error(self):
        """Test Ollama chat error handling."""
        import pytest
        import requests

        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Connection failed")

            client = LLMClient(model="llama3.2", provider="ollama")
            with pytest.raises(RuntimeError, match="Ollama API error"):
                client.chat([Message(role="user", content="Hello")])

    def test_ollama_model_override_from_gemini(self):
        """Test that gemini model is replaced with ollama default."""
        client = LLMClient(model="gemini-2.0-flash", provider="ollama")
        assert "gemini" not in client.model.lower()

    def test_ollama_custom_base_url(self):
        """Test Ollama with custom base URL."""
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://custom:8080"}):
            client = LLMClient(model="llama3.2", provider="ollama")
            assert client._ollama_base_url == "http://custom:8080"


class TestGeminiProvider:
    """Tests for Gemini provider (mocked)."""

    def test_gemini_requires_api_key(self):
        """Test that Gemini requires API key."""
        import pytest

        with patch.dict(os.environ, {}, clear=True):
            # Remove any API keys
            os.environ.pop("GEMINI_API_KEY", None)
            os.environ.pop("GOOGLE_API_KEY", None)

            with pytest.raises(RuntimeError, match="APIキーが見つかりません"):
                LLMClient(provider="gemini")

    def test_gemini_init_with_api_key(self):
        """Test Gemini initialization with API key."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch("google.genai.Client") as mock_client:
                client = LLMClient(provider="gemini")
                assert client.provider == "gemini"
                mock_client.assert_called_once_with(api_key="test-key")


class TestProviderSwitching:
    """Tests for provider switching logic."""

    def test_default_provider_is_gemini(self):
        """Test that default provider is gemini."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LLM_PROVIDER", None)
            os.environ["GEMINI_API_KEY"] = "test-key"
            with patch("google.genai.Client"):
                client = LLMClient()
                assert client.provider == "gemini"

    def test_env_provider_ollama(self):
        """Test LLM_PROVIDER=ollama is respected."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
            client = LLMClient(model="llama3.2")
            assert client.provider == "ollama"

    def test_invalid_provider_raises(self):
        """Test that invalid provider raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMClient(provider="invalid")
