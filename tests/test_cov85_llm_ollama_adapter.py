"""Coverage tests for jarvis_core.llm.ollama_adapter."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from jarvis_core.llm.ollama_adapter import OllamaAdapter, OllamaConfig, get_ollama_adapter


class TestOllamaConfig:
    def test_defaults(self) -> None:
        cfg = OllamaConfig()
        assert cfg.base_url == "http://127.0.0.1:11434"
        assert cfg.model == "llama3.2"
        assert cfg.timeout == 120
        assert cfg.max_retries == 3

    def test_custom(self) -> None:
        cfg = OllamaConfig(base_url="http://host:1234", model="mistral", timeout=60)
        assert cfg.base_url == "http://host:1234"
        assert cfg.model == "mistral"


class TestOllamaAdapterInit:
    def test_default_config(self) -> None:
        adapter = OllamaAdapter()
        assert adapter.base_url is not None
        assert adapter.model is not None

    def test_custom_config(self) -> None:
        cfg = OllamaConfig(base_url="http://test:5555", model="phi")
        adapter = OllamaAdapter(config=cfg)
        assert adapter.base_url == "http://test:5555"
        assert adapter.model == "phi"


class TestIsAvailable:
    def test_available(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.get", return_value=mock_resp):
            assert adapter.is_available() is True
        # Cached
        assert adapter.is_available() is True

    def test_unavailable(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        with patch("requests.get", side_effect=ConnectionError("refused")):
            assert adapter.is_available() is False

    def test_bad_status(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("requests.get", return_value=mock_resp):
            assert adapter.is_available() is False


class TestListModels:
    def test_unavailable(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        adapter._available = False
        assert adapter.list_models() == []

    def test_success(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        adapter._available = True
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "llama3"}, {"name": "phi"}]}
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            models = adapter.list_models()
        assert "llama3" in models

    def test_error(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        adapter._available = True
        with patch("requests.get", side_effect=Exception("fail")):
            assert adapter.list_models() == []


class TestGenerate:
    def test_success(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Hello world"}
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.post", return_value=mock_resp):
            result = adapter.generate("Say hello")
        assert result == "Hello world"

    def test_custom_model(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "OK"}
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.post", return_value=mock_resp) as mock_post:
            adapter.generate("test", model="custom-model", options={"top_p": 0.9})
        call_data = mock_post.call_args[1]["json"]
        assert call_data["model"] == "custom-model"

    def test_error(self) -> None:
        import requests as req_mod

        adapter = OllamaAdapter(OllamaConfig())
        with patch("requests.post", side_effect=req_mod.RequestException("timeout")):
            with pytest.raises(RuntimeError, match="Ollama API error"):
                adapter.generate("test")


class TestGenerateStream:
    def test_success(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        lines = [
            json.dumps({"response": "Hello"}).encode(),
            json.dumps({"response": " world", "done": True}).encode(),
        ]
        mock_resp = MagicMock()
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("requests.post", return_value=mock_resp):
            chunks = list(adapter.generate_stream("test"))
        assert "Hello" in chunks
        assert " world" in chunks

    def test_error(self) -> None:
        import requests as req_mod

        adapter = OllamaAdapter(OllamaConfig())
        with patch("requests.post", side_effect=req_mod.RequestException("err")):
            with pytest.raises(RuntimeError):
                list(adapter.generate_stream("test"))


class TestChat:
    def test_success(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": {"content": "Hi there"}}
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.post", return_value=mock_resp):
            result = adapter.chat([{"role": "user", "content": "Hello"}])
        assert result == "Hi there"

    def test_error(self) -> None:
        import requests as req_mod

        adapter = OllamaAdapter(OllamaConfig())
        with patch("requests.post", side_effect=req_mod.RequestException("err")):
            with pytest.raises(RuntimeError):
                adapter.chat([{"role": "user", "content": "test"}])


class TestChatStream:
    def test_success(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        lines = [
            json.dumps({"message": {"content": "Hi"}}).encode(),
            json.dumps({"message": {"content": ""}, "done": True}).encode(),
        ]
        mock_resp = MagicMock()
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("requests.post", return_value=mock_resp):
            chunks = list(adapter.chat_stream([{"role": "user", "content": "test"}]))
        assert "Hi" in chunks

    def test_error(self) -> None:
        import requests as req_mod

        adapter = OllamaAdapter(OllamaConfig())
        with patch("requests.post", side_effect=req_mod.RequestException("err")):
            with pytest.raises(RuntimeError):
                list(adapter.chat_stream([{"role": "user", "content": "test"}]))


class TestEmbeddings:
    def test_success(self) -> None:
        adapter = OllamaAdapter(OllamaConfig())
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.post", return_value=mock_resp):
            result = adapter.embeddings("test text")
        assert result == [0.1, 0.2, 0.3]

    def test_error(self) -> None:
        import requests as req_mod

        adapter = OllamaAdapter(OllamaConfig())
        with patch("requests.post", side_effect=req_mod.RequestException("err")):
            with pytest.raises(RuntimeError):
                adapter.embeddings("test")


class TestGetOllamaAdapter:
    def test_singleton(self) -> None:
        import jarvis_core.llm.ollama_adapter as mod

        mod._default_adapter = None
        a1 = get_ollama_adapter()
        a2 = get_ollama_adapter()
        assert a1 is a2
        mod._default_adapter = None  # cleanup
