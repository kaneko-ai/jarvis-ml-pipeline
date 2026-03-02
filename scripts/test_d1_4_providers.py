import sys
import os
import time
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from jarvis_core.llm.litellm_client import completion, completion_structured
from jarvis_core.llm.structured_models import PaperSummaryLLM

results = []

# --- Test 1: Gemini via LiteLLM ---
print("=" * 50)
print("[Test 1/3] Gemini via LiteLLM")
try:
    resp = completion(
        "What is PD-1 immunotherapy? Reply in exactly 50 words.",
        model="gemini/gemini-2.0-flash",
    )
    print(f"  OK: {resp[:100]}...")
    results.append(("Gemini-LiteLLM", True))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Gemini-LiteLLM", False))

time.sleep(3)

# --- Test 2: Structured Output (Gemini + Instructor) ---
print("=" * 50)
print("[Test 2/3] Structured Output via Instructor + Gemini")
try:
    paper = completion_structured(
        prompt=(
            "Summarize this paper: "
            "PD-1 is an immune checkpoint receptor that negatively "
            "regulates T cell activation. Anti-PD-1 antibodies have "
            "shown remarkable efficacy in various cancers."
        ),
        response_model=PaperSummaryLLM,
        model="gemini/gemini-2.0-flash",
    )
    print(f"  title_ja: {paper.title_ja}")
    print(f"  summary_ja: {paper.summary_ja[:80]}...")
    print(f"  key_findings: {len(paper.key_findings)} items")
    print(f"  relevance_score: {paper.relevance_score}")
    results.append(("Structured-Output", True))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Structured-Output", False))

time.sleep(3)

# --- Test 3: Existing LLMClient (backward compat) ---
print("=" * 50)
print("[Test 3/3] Existing LLMClient (Gemini direct)")
try:
    from jarvis_core.llm.llm_utils import LLMClient, Message
    client = LLMClient(provider="gemini")
    resp = client.chat([Message(role="user", content="Say hello in 10 words.")])
    print(f"  OK: {resp[:100]}...")
    results.append(("LLMClient-Legacy", True))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("LLMClient-Legacy", False))

# --- Summary ---
print("=" * 50)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\nResults: {passed}/{total} passed")
for name, ok in results:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}")

if passed >= 2:
    print("\nLLM foundation ready! Proceed to D1-5.")
else:
    print("\nCheck API keys in .env")
