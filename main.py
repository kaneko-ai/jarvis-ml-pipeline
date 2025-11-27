# main.py
from router import Router
from llm import LLMClient


def run_jarvis(user_task: str) -> str:
    # ここで使用するモデルを指定
    llm = LLMClient(model="gemini-2.0-flash")
    router = Router(llm)
    result = router.run(user_task)
    return result.answer


if __name__ == "__main__":
    print("Jarvis v1.0 - 単発タスクモード")
    print("日本語でタスク内容を入力してください。空行で終了します。")

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    task = "\n".join(lines).strip()
    if not task:
        exit(0)

    answer = run_jarvis(task)
    print("\n=== Jarvis の回答 ===\n")
    print(answer)
