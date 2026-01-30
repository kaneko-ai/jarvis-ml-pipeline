"""
llama.cpp Adapter for JARVIS Local-First LLM

CPU/GPU環境でのローカルLLM推論を担当。
Ollamaが利用できない場合のフォールバック。
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LlamaCppConfig:
    """llama.cpp設定."""

    model_path: str | None = None
    n_ctx: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 0  # 0 = CPU only
    verbose: bool = False


class LlamaCppAdapter:
    """llama.cppアダプター.

    llama-cpp-pythonを使用したローカルLLM推論を提供。
    Ollamaが利用できない環境でのフォールバック用。
    """

    def __init__(self, config: LlamaCppConfig | None = None):
        self.config = config or LlamaCppConfig(
            model_path=os.getenv("LLAMACPP_MODEL_PATH"),
            n_threads=int(os.getenv("LLAMACPP_THREADS", "4")),
            n_gpu_layers=int(os.getenv("LLAMACPP_GPU_LAYERS", "0")),
        )
        self._llm = None
        self._available: bool | None = None

    def is_available(self) -> bool:
        """llama-cpp-pythonが利用可能かチェック."""
        if self._available is not None:
            return self._available

        try:
            import llama_cpp  # noqa: F401

            self._available = True
            logger.info("llama-cpp-python is available")
            return True
        except ImportError:
            logger.warning("llama-cpp-python not installed")
            self._available = False
            return False

    def _ensure_model(self) -> None:
        """モデルのロード."""
        if self._llm is not None:
            return

        if not self.config.model_path:
            raise RuntimeError("LLAMACPP_MODEL_PATH not set. Please set the path to a GGUF model.")

        model_path = Path(self.config.model_path)
        if not model_path.exists():
            raise RuntimeError(f"Model file not found: {model_path}")

        try:
            from llama_cpp import Llama

            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                verbose=self.config.verbose,
            )
            logger.info(f"Loaded model: {model_path.name}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to load llama.cpp model: {e}") from e

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: list[str] | None = None,
        **kwargs,
    ) -> str:
        """テキスト生成."""
        if not self.is_available():
            raise RuntimeError("llama-cpp-python not available")

        self._ensure_model()

        try:
            output = self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
                echo=False,
            )
            return output["choices"][0]["text"]
        except Exception as e:
            logger.error(f"llama.cpp generate error: {e}")
            raise RuntimeError(f"llama.cpp error: {e}") from e

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: list[str] | None = None,
        **kwargs,
    ) -> Generator[str, None, None]:
        """ストリーミング生成."""
        if not self.is_available():
            raise RuntimeError("llama-cpp-python not available")

        self._ensure_model()

        try:
            for output in self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
                echo=False,
                stream=True,
            ):
                token = output["choices"][0]["text"]
                if token:
                    yield token
        except Exception as e:
            logger.error(f"llama.cpp stream error: {e}")
            raise RuntimeError(f"llama.cpp error: {e}") from e

    def chat(
        self, messages: list[dict], max_tokens: int = 512, temperature: float = 0.7, **kwargs
    ) -> str:
        """チャット形式で生成."""
        prompt = self._messages_to_prompt(messages)
        return self.generate(prompt, max_tokens=max_tokens, temperature=temperature, **kwargs)

    def _messages_to_prompt(self, messages: list[dict]) -> str:
        """メッセージリストをプロンプト形式に変換（ChatML形式）."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")

        # アシスタントの応答を促す
        parts.append("<|im_start|>assistant\n")
        return "\n".join(parts)


# シングルトンインスタンス
_default_adapter: LlamaCppAdapter | None = None


def get_llamacpp_adapter() -> LlamaCppAdapter:
    """デフォルトのllama.cppアダプターを取得."""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = LlamaCppAdapter()
    return _default_adapter