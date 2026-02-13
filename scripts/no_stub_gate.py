#!/usr/bin/env python
"""No-Stub quality gate for ops_extract related code."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TODO_RE = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)
OK_TRUE_RE = re.compile(r"['\"]ok['\"]\s*:\s*True\b")
DUMMY_ID_RE = re.compile(r"\bdummy[_-]?[a-z0-9]*\b", re.IGNORECASE)


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class AllowRule:
    path_glob: str
    code: str
    line: int | None
    reason: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_allowlist(path: Path) -> list[AllowRule]:
    if not path.exists():
        return []

    rules: list[AllowRule] = []
    for idx, raw in enumerate(_read_text(path).splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 4:
            raise ValueError(f"Invalid allowlist format at {path}:{idx}")
        path_glob, code, line_text, reason = parts
        if not reason:
            raise ValueError(f"Allowlist reason missing at {path}:{idx}")
        line_no = None if line_text in {"*", ""} else int(line_text)
        rules.append(AllowRule(path_glob=path_glob, code=code, line=line_no, reason=reason))
    return rules


def _is_allowed(v: Violation, rules: list[AllowRule]) -> bool:
    candidate = Path(v.file).as_posix()
    for rule in rules:
        if not Path(candidate).match(rule.path_glob):
            continue
        if rule.code != "*" and rule.code != v.code:
            continue
        if rule.line is not None and rule.line != v.line:
            continue
        return True
    return False


def _detect_comment_markers(path: Path, text: str) -> list[Violation]:
    violations: list[Violation] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if TODO_RE.search(line):
            violations.append(
                Violation(
                    file=path.as_posix(),
                    line=i,
                    code="NO_STUB_TODO",
                    message="TODO/FIXME marker found",
                )
            )
    return violations


def _is_name_constant(node: ast.AST, value: object) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _detect_ast_stubs(path: Path, text: str) -> list[Violation]:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [
            Violation(
                file=path.as_posix(),
                line=exc.lineno or 1,
                code="NO_STUB_PARSE_ERROR",
                message=f"parse error: {exc.msg}",
            )
        ]

    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                violations.append(
                    Violation(
                        file=path.as_posix(),
                        line=stmt.lineno,
                        code="NO_STUB_PASS_ONLY",
                        message=f"pass-only function: {node.name}",
                    )
                )
            elif isinstance(stmt, ast.Return):
                if stmt.value is None or (stmt.value and _is_name_constant(stmt.value, None)):
                    violations.append(
                        Violation(
                            file=path.as_posix(),
                            line=stmt.lineno,
                            code="NO_STUB_RETURN_NONE_ONLY",
                            message=f"return-None-only function: {node.name}",
                        )
                    )
                elif isinstance(stmt.value, ast.Constant) and isinstance(
                    stmt.value.value, (bool, int, float, str)
                ):
                    violations.append(
                        Violation(
                            file=path.as_posix(),
                            line=stmt.lineno,
                            code="NO_STUB_RETURN_CONST_ONLY",
                            message=f"return-constant-only function: {node.name}",
                        )
                    )

        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            keys = node.value.keys
            values = node.value.values
            for key, value in zip(keys, values):
                if isinstance(key, ast.Constant) and str(key.value) == "ok":
                    if isinstance(value, ast.Constant) and value.value is True:
                        violations.append(
                            Violation(
                                file=path.as_posix(),
                                line=node.lineno,
                                code="NO_STUB_OK_TRUE_RESPONSE",
                                message="return {'ok': True} style response detected",
                            )
                        )
    return violations


def _detect_text_patterns(path: Path, text: str) -> list[Violation]:
    violations: list[Violation] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if DUMMY_ID_RE.search(line) and "allow_dummy" not in line:
            violations.append(
                Violation(
                    file=path.as_posix(),
                    line=i,
                    code="NO_STUB_DUMMY_ID",
                    message="dummy-like identifier found",
                )
            )
        if OK_TRUE_RE.search(line):
            violations.append(
                Violation(
                    file=path.as_posix(),
                    line=i,
                    code="NO_STUB_OK_TRUE_LITERAL",
                    message="ok:true/ok:True literal found",
                )
            )
    return violations


def _iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            yield path
            continue
        if path.is_dir():
            for file in path.rglob("*.py"):
                if any(token in file.parts for token in ("venv", ".venv", "node_modules", ".git")):
                    continue
                yield file


def run_gate(paths: list[Path], allowlist_path: Path) -> list[Violation]:
    allow_rules = _load_allowlist(allowlist_path)
    violations: list[Violation] = []
    for file in _iter_python_files(paths):
        text = _read_text(file)
        violations.extend(_detect_comment_markers(file, text))
        violations.extend(_detect_ast_stubs(file, text))
        violations.extend(_detect_text_patterns(file, text))
    return [v for v in violations if not _is_allowed(v, allow_rules)]


def main() -> int:
    parser = argparse.ArgumentParser(description="No-Stub quality gate")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["jarvis_core/ops_extract"],
        help="files/directories to scan",
    )
    parser.add_argument(
        "--allowlist",
        default="configs/no_stub_allowlist.txt",
        help="allowlist path",
    )
    args = parser.parse_args()

    scan_paths = [Path(p) for p in args.paths]
    violations = run_gate(scan_paths, Path(args.allowlist))
    if not violations:
        print("NO_STUB_GATE: PASS")
        return 0

    print(f"NO_STUB_GATE: FAIL ({len(violations)} violations)")
    for item in sorted(violations, key=lambda x: (x.file, x.line, x.code)):
        print(f"{item.file}:{item.line}: {item.code}: {item.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
