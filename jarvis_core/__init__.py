# jarvis_core/__init__.py
from .llm import LLMClient
from .router import Router

def run_jarvis(task: str) -> str:
    """
    Jarvis のコア処理を 1 関数にまとめたラッパー。
    どの環境（ローカル / 大学PC / antigravity）からも
    これだけ呼べば同じ挙動になる。
    """
    # ここで使うモデルを一元管理
    llm = LLMClient(model="gemini-2.0-flash")  # いま使っている設定
    router = Router(llm)
    result = router.run(task)
    return result.answer
