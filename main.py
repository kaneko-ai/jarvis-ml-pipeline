#!/usr/bin/env python
"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
WARNING: このファイルは開発デモ専用です。本番環境では使用しないでください。
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

本番環境での実行には jarvis_cli.py を使用してください:
  python jarvis_cli.py run --goal "your research question"

詳細: docs/GOLDEN_PATH.md
"""
# main.py - DEMO ONLY (本番禁止)
import warnings
from jarvis_core import run_jarvis


def main() -> None:
    # デモ使用の警告を表示
    warnings.warn(
        "main.py はデモ専用です。本番環境では jarvis_cli.py を使用してください。",
        DeprecationWarning,
        stacklevel=2,
    )
    print("=" * 60)
    print("⚠️  DEMO MODE - 本番環境では jarvis_cli.py を使用してください")
    print("=" * 60)
    print()
    print("Jarvis v1.0 - 単発タスクモード (DEMO)")
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
