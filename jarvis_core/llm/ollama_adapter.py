"""
Ollama Adapter for JARVIS Local-First LLM

ローカルOllamaサーバーとの通信を担当。
ストリーミング生成、モデル可用性チェック、エラーハンドリングを含む。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Ollama設定."""
    base_url: str = "http://127.0.0.1:11434"
    model: str = "llama3.2"
    timeout: int = 120
    max_retries: int = 3


class OllamaAdapter:
    """Ollamaアダプター.
    
    ローカルOllamaサーバーを使用したLLM推論を提供。
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        )
        self._available: Optional[bool] = None
    
    @property
    def base_url(self) -> str:
        return self.config.base_url
    
    @property
    def model(self) -> str:
        return self.config.model
    
    def is_available(self) -> bool:
        """Ollamaサーバーが利用可能かチェック."""
        if self._available is not None:
            return self._available
        
        try:
            import requests
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            self._available = response.status_code == 200
            if self._available:
                logger.info(f"Ollama server available at {self.base_url}")
            return self._available
        except Exception as e:
            logger.warning(f"Ollama server not available: {e}")
            self._available = False
            return False
    
    def list_models(self) -> List[str]:
        """利用可能なモデル一覧を取得."""
        if not self.is_available():
            return []
        
        try:
            import requests
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """テキスト生成.
        
        Args:
            prompt: 入力プロンプト
            model: モデル名（省略時はデフォルト）
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            
        Returns:
            生成されたテキスト
        """
        import requests
        
        model = model or self.config.model
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                **kwargs.get("options", {}),
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except requests.RequestException as e:
            logger.error(f"Ollama generate error: {e}")
            raise RuntimeError(f"Ollama API error: {e}") from e
    
    def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """ストリーミング生成.
        
        Args:
            prompt: 入力プロンプト
            model: モデル名
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            
        Yields:
            生成されたテキストチャンク
        """
        import json
        import requests
        
        model = model or self.config.model
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        try:
            with requests.post(
                url,
                json=payload,
                timeout=self.config.timeout,
                stream=True
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
        except requests.RequestException as e:
            logger.error(f"Ollama stream error: {e}")
            raise RuntimeError(f"Ollama API error: {e}") from e
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """チャット形式で生成.
        
        Args:
            messages: メッセージリスト [{"role": "user", "content": "..."}]
            model: モデル名
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            
        Returns:
            生成されたレスポンス
        """
        import requests
        
        model = model or self.config.model
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except requests.RequestException as e:
            logger.error(f"Ollama chat error: {e}")
            raise RuntimeError(f"Ollama API error: {e}") from e
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """ストリーミングチャット.
        
        Yields:
            生成されたテキストチャンク
        """
        import json
        import requests
        
        model = model or self.config.model
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        try:
            with requests.post(
                url,
                json=payload,
                timeout=self.config.timeout,
                stream=True
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done", False):
                            break
        except requests.RequestException as e:
            logger.error(f"Ollama chat stream error: {e}")
            raise RuntimeError(f"Ollama API error: {e}") from e
    
    def embeddings(
        self,
        text: str,
        model: str = "nomic-embed-text"
    ) -> List[float]:
        """テキスト埋め込み生成.
        
        Args:
            text: 入力テキスト
            model: 埋め込みモデル名
            
        Returns:
            埋め込みベクトル
        """
        import requests
        
        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": model,
            "prompt": text,
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except requests.RequestException as e:
            logger.error(f"Ollama embeddings error: {e}")
            raise RuntimeError(f"Ollama API error: {e}") from e


# シングルトンインスタンス
_default_adapter: Optional[OllamaAdapter] = None


def get_ollama_adapter() -> OllamaAdapter:
    """デフォルトのOllamaアダプターを取得."""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = OllamaAdapter()
    return _default_adapter
