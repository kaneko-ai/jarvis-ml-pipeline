"""
LLM Provider abstraction for JARVIS.
Supports: gemini (default), codex (via Codex CLI with gpt-5.2)
"""
import os
import json
import subprocess
import time


class LLMProvider:
    """Base class for LLM providers."""

    def summarize(self, title: str, abstract: str, lang: str = "ja") -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Gemini API provider (existing behavior)."""

    def __init__(self):
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def summarize(self, title: str, abstract: str, lang: str = "ja") -> str:
        prompt = (
            f"以下の論文を日本語で3行で要約してください。\n\n"
            f"タイトル: {title}\n"
            f"アブストラクト: {abstract}\n\n"
            f"要約:"
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"[要約エラー: {e}]"


class CodexProvider(LLMProvider):
    """Codex CLI provider - uses gpt-5.2 via ChatGPT Plus subscription."""

    def __init__(self, model="gpt-5.2"):
        self.model = model
        # shell=True lets Windows find codex.cmd via PATH
        try:
            result = subprocess.run(
                "codex --version",
                capture_output=True, text=True, timeout=10,
                shell=True
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"codex CLI returned error: {result.stderr.strip()}"
                )
            self.codex_version = result.stdout.strip()
        except FileNotFoundError:
            raise RuntimeError(
                "codex CLI is not installed. Run: npm i -g @openai/codex"
            )

    def summarize(self, title: str, abstract: str, lang: str = "ja") -> str:
        prompt = (
            f"以下の論文を日本語で3行だけで要約してください。"
            f"要約のみを出力し、それ以外は何も出力しないでください。\n\n"
            f"タイトル: {title}\n"
            f"アブストラクト: {abstract}"
        )
        try:
            # Use codex exec with gpt-5.2 model for reasoning
            # --skip-git-repo-check: not a coding task
            # -m: model selection
            cmd = (
                f'codex exec --skip-git-repo-check '
                f'-m {self.model} '
                f'-o NUL '
                f'"{prompt}"'
            )
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=120,
                shell=True,
                cwd=os.getcwd()
            )
            output = result.stdout.strip()
            if result.returncode == 0 and output:
                # codex exec may include extra formatting, extract just the text
                lines = [l for l in output.split("\n") if l.strip()]
                return "\n".join(lines)
            else:
                err = result.stderr.strip() if result.stderr else "no output"
                return f"[Codex要約エラー: {err}]"
        except subprocess.TimeoutExpired:
            return "[Codex要約エラー: タイムアウト(120秒)]"
        except Exception as e:
            return f"[Codex要約エラー: {e}]"


def get_provider(name: str = "gemini") -> LLMProvider:
    """Get LLM provider by name.

    Args:
        name: 'gemini' or 'codex'
              codex uses gpt-5.2 via Codex CLI (ChatGPT Plus required)
    """
    if name == "gemini":
        return GeminiProvider()
    elif name == "codex":
        return CodexProvider(model="gpt-5.2")
    else:
        raise ValueError(
            f"Unknown provider: {name}. Available: gemini, codex"
        )
