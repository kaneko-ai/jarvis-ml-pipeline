import pathlib

target = pathlib.Path("jarvis_core/llm/litellm_client.py")
target.parent.mkdir(parents=True, exist_ok=True)

code = '''\
"""LiteLLM unified client for JARVIS Research OS."""
from __future__ import annotations
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def completion(
    prompt: str,
    model: Optional[str] = None,
    system: str = "You are a research assistant.",
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> str:
    """Unified LLM completion via LiteLLM."""
    import litellm

    if model is None:
        model = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    response = litellm.completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def completion_structured(
    prompt: str,
    response_model,
    model: Optional[str] = None,
    system: str = "You are a research assistant.",
) -> object:
    """Structured output via Instructor + LiteLLM."""
    import instructor
    import litellm

    if model is None:
        model = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")

    client = instructor.from_litellm(litellm.completion)
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        response_model=response_model,
    )
'''

target.write_text(code, encoding="utf-8")
print(f"Created: {target} ({target.stat().st_size} bytes)")
