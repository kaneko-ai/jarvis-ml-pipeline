import sys
sys.path.insert(0, ".")

from jarvis_core.llm.structured_models import (
    EvidenceGradeLLM,
    PaperSummaryLLM,
    ContradictionResultLLM,
    CitationStanceLLM,
)
print("All structured models imported OK")

from jarvis_core.llm.litellm_client import completion, completion_structured
print("LiteLLM client imported OK")

from importlib.metadata import version
print(f"litellm version: {version('litellm')}")
print(f"instructor version: {version('instructor')}")
print(f"pydantic-ai version: {version('pydantic-ai')}")

print("\nD1-3 complete!")
