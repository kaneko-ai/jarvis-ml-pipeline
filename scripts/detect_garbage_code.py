#!/usr/bin/env python
"""Detect placeholder or garbage code patterns."""

from __future__ import annotations

import ast
import sys
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

MSG_PASS = "ダミー実装（passのみ）"
MSG_RETURN_NONE = "ダミー実装（return Noneのみ）"
MSG_RETURN_CONST = "ダミー実装（return {value}のみ）"
MSG_EXCEPT_PASS = "握りつぶしexcept（except: pass）"


class GarbageDetector(ast.NodeVisitor):
    """AST visitor for detecting low-quality placeholder logic."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.issues: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in WHITELIST_FUNCTIONS:
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                self.issues.append(f"{node.lineno}:{node.name}: {MSG_PASS}")
            self.generic_visit(node)
            return

        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                self.issues.append(f"{node.lineno}:{node.name}: {MSG_PASS}")
            elif isinstance(stmt, ast.Return):
                # Python 3.8+ represents `return None` as ast.Constant(None),
                # while older code could expose stmt.value as None.
                if stmt.value is None:
                    self.issues.append(f"{node.lineno}:{node.name}: {MSG_RETURN_NONE}")
                elif isinstance(stmt.value, ast.Constant):
                    value = stmt.value.value
                    if value is None:
                        self.issues.append(f"{node.lineno}:{node.name}: {MSG_RETURN_NONE}")
                    elif isinstance(value, (bool, int)):
                        self.issues.append(
                            f"{node.lineno}:{node.name}: {MSG_RETURN_CONST.format(value=value)}"
                        )

        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            if isinstance(node.type, ast.Name) and node.type.id in {"ImportError", "AttributeError"}:
                self.generic_visit(node)
                return
            self.issues.append(f"{node.lineno}: {MSG_EXCEPT_PASS}")
        self.generic_visit(node)


def scan_file(path: Path) -> list[str]:
    """Scan a single Python file."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"{path}: SyntaxError: {exc}"]
    except UnicodeDecodeError:
        return []

    detector = GarbageDetector(str(path))
    detector.visit(tree)
    return [f"{path}:{issue}" for issue in detector.issues]


def main() -> int:
    issues: list[str] = []
    for py_file in Path("jarvis_core").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        issues.extend(scan_file(py_file))

    if issues:
        print("=== ゴミコード検出 ===")
        for issue in sorted(issues):
            print(issue)
        print(f"\n合計 {len(issues)} 件")
        return 1

    print("ゴミコードなし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
