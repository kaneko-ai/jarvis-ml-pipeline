# main.py
from jarvis_core import run_jarvis

def main() -> None:
    print("Jarvis v1.0 - 単発タスクモード")
    print("日本語でタスク内容を入力してください。空行で終了します。")

    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)

    task = "\n".join(lines).strip()
    if not task:
        return

    answer = run_jarvis(task)
    print("\n=== Jarvis の回答 ===\n")
    print(answer)

if __name__ == "__main__":
    main()
