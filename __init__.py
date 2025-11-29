from .llm import LLMClient
from .router import Router


def run_jarvis(task: str) -> str:
    llm = LLMClient(model="gemini-2.0-flash")
    router = Router(llm)
    result = router.run(task)
    return result.answer
