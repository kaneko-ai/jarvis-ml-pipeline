# llm.py
"""LLM client with provider switching support.

Supports:
- gemini (default): Google Gemini API
- ollama: Local Ollama server (http://127.0.0.1:11434)

Set LLM_PROVIDER environment variable to switch providers.
"""
import os
from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str


def _get_provider() -> str:
    """Get LLM provider from environment variable."""
    return os.getenv("LLM_PROVIDER", "gemini").lower()


class MockLLM:
    """Stateful LLM Mock for testing complex scenarios."""
    
    def __init__(self):
        self.responses: list[str] = []
        self.failures_remaining: int = 0
        self.error_message: str = "Simulated LLM Error"
        self.budget_remaining: float = 100.0
        self.call_count: int = 0
        
    def configure(self, failures: int = 0, error_msg: str = "Simulated LLM Error", budget: float = 100.0):
        """Configure mock behavior."""
        self.failures_remaining = failures
        self.error_message = error_msg
        self.budget_remaining = budget
        
    def generate(self, prompt: str) -> str:
        """Generate a response with stateful behavior."""
        self.call_count += 1
        
        if self.budget_remaining <= 0:
            raise RuntimeError("Budget exhausted (mocked)")
            
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise RuntimeError(self.error_message)
            
        self.budget_remaining -= 1.0  # Simple cost simulation
        
        # Trigger-based legacy support
        if "trigger_budget_limit" in prompt.lower():
            self.budget_remaining = 0
            raise RuntimeError("Budget exhausted (simulated)")

        if "trigger_empty" in prompt.lower():
            return ""

        if "trigger_retry" in prompt.lower():
            if self.call_count == 1:
                raise RuntimeError("Temporary mock error for retry testing")
            return f"Successful retry response to: {prompt[:30]}... [chunk:mock-chunk-id-001]"

        if "plan" in prompt.lower():
            return "Mock Plan:\n1. Step A\n2. [chunk:mock-chunk-id-001]\n[SUCCESS]"
            
        return f"Mock response ({self.call_count}) to: {prompt[:50]}... [chunk:mock-chunk-id-001]"


class LLMClient:
    """LLM client with provider switching.

    Args:
        model: Model name (provider-specific).
        provider: Override LLM_PROVIDER env var if specified.
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        provider: str | None = None,
    ) -> None:
        self.provider = provider or _get_provider()
        self.model = model
        self._call_counts: dict[str, int] = {}  # Track calls per task_id/goal for triggers

        if self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "mock":
            self._init_mock()
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _init_gemini(self) -> None:
        """Initialize Gemini client."""
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Gemini APIキーが見つかりません。環境変数 GEMINI_API_KEY か GOOGLE_API_KEY を設定してください。"
            )
        self._gemini_client = genai.Client(api_key=api_key)

    def _init_ollama(self) -> None:
        """Initialize Ollama client."""
        self._ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        # Default model for ollama if gemini model specified
        if "gemini" in self.model.lower():
            self.model = os.getenv("OLLAMA_MODEL", "llama3.2")

    def _init_mock(self) -> None:
        """Initialize Mock client."""
        self._mock_engine = MockLLM()

    def chat(self, messages: list[Message]) -> str:
        """Send chat messages and return response text.

        Args:
            messages: List of Message objects with role and content.

        Returns:
            Response text from the LLM.
        """
        if self.provider == "gemini":
            return self._chat_gemini(messages)
        elif self.provider == "ollama":
            return self._chat_ollama(messages)
        elif self.provider == "mock":
            return self._chat_mock(messages)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _chat_gemini(self, messages: list[Message]) -> str:
        """Chat via Gemini API."""
        from google.genai import errors

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
            response = self._gemini_client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
        except (errors.ServerError, errors.ClientError):
            # Fallback to gemini-2.0-flash on error
            backup_model = "gemini-2.0-flash"
            response = self._gemini_client.models.generate_content(
                model=backup_model,
                contents=full_prompt,
            )

        return response.text or ""

    def _chat_ollama(self, messages: list[Message]) -> str:
        """Chat via Ollama API.

        Uses the /api/chat endpoint with streaming disabled.
        """
        import requests

        ollama_messages = []
        for m in messages:
            ollama_messages.append(
                {
                    "role": m.role,
                    "content": m.content,
                }
            )

        url = f"{self._ollama_base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}") from e

    def _chat_mock(self, messages: list[Message]) -> str:
        """Return a mock response using MockLLM engine."""
        last_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "No input")
        return self._mock_engine.generate(last_user_msg)
