#!/usr/bin/env python
"""ゴミコード検出スクリプト。"""

from __future__ import annotations

import ast
from pathlib import Path

WHITELIST_FUNCTIONS = {
    "name",
    "__str__",
    "__repr__",
    "__hash__",
    "__bool__",
    "__len__",
    "__contains__",
    "__enter__",
    "__exit__",
    "__eq__",
    "__ne__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
    "verify",
    "initialize",
    "setup",
    "teardown",
    "cleanup",
    "validate",
}


class GarbageDetector(ast.NodeVisitor):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.issues: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # ホワイトリスト関数でも pass のみは検出対象
        if node.name in WHITELIST_FUNCTIONS:
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                self.issues.append(f"{node.lineno}:{node.name}: ホワイトリスト関数だがpassのみ")
            self.generic_visit(node)
            return

        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                self.issues.append(f"{node.lineno}:{node.name}: ダミー実装（passのみ）")
            elif isinstance(stmt, ast.Return):
                return_value = stmt.value
                if return_value is None or (
                    isinstance(return_value, ast.Constant) and return_value.value is None
                ):
                    self.issues.append(f"{node.lineno}:{node.name}: ダミー実装（return Noneのみ）")
                elif isinstance(return_value, ast.Constant):
                    if isinstance(return_value.value, str):
                        # 1行文字列リテラル return は除外
                        pass
                    elif (
                        isinstance(return_value.value, (bool, int))
                        and node.name not in WHITELIST_FUNCTIONS
                    ):
                        self.issues.append(
                            f"{node.lineno}:{node.name}: ダミー実装（return {return_value.value}のみ）"
                        )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            if isinstance(node.type, ast.Name) and node.type.id in (
                "ImportError",
                "AttributeError",
            ):
                self.generic_visit(node)
                return
            self.issues.append(f"{node.lineno}: 握りつぶしexcept（except: pass）")
        self.generic_visit(node)


def scan_file(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{path}: SyntaxError: {exc}"]
    except UnicodeDecodeError:
        return []

    detector = GarbageDetector(str(path))
    detector.visit(tree)
    return [f"{path}:{issue}" for issue in detector.issues]


def main() -> None:
    issues: list[str] = []
    for py_file in Path("jarvis_core").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        issues.extend(scan_file(py_file))

    if issues:
        print("=== ゴミコード検出 ===")
        for issue in sorted(issues):
            print(issue)
        print(f"\n合計 {len(issues)} 件の問題が見つかりました。")
        raise SystemExit(1)

    print("ゴミコードなし")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
