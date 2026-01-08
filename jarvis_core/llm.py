# llm.py
import os
from dataclasses import dataclass
from typing import Literal

from google import genai
from google.genai import errors

Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str


class LLMClient:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        """
        Gemini 用のクライアント。
        model 引数で使用モデルを指定できる。
        """
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Gemini APIキーが見つかりません。環境変数 GEMINI_API_KEY か GOOGLE_API_KEY を設定してください。"
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def chat(self, messages: list[Message]) -> str:
        """
        単純なチャットラッパー。
        system / user / assistant を簡単なタグ付きテキストに連結して投げる。
        """
        prompt_parts: list[str] = []
        for m in messages:
            prefix = {
                "system": "[SYSTEM]",
                "user": "[USER]",
                "assistant": "[ASSISTANT]",
            }[m.role]
            prompt_parts.append(f"{prefix}\n{m.content}\n")

        full_prompt = "\n".join(prompt_parts)

        try:
            # 第一候補のモデルで実行
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
        except (errors.ServerError, errors.ClientError):
            # モデル過負荷や NOT_FOUND の場合は gemini-2.0-flash にフォールバック
            backup_model = "gemini-2.0-flash"
            response = self.client.models.generate_content(
                model=backup_model,
                contents=full_prompt,
            )

        return response.text or ""
