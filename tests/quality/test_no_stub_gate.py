from __future__ import annotations

from pathlib import Path

from scripts.no_stub_gate import run_gate


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_no_stub_gate_detects_todo(tmp_path: Path) -> None:
    target = tmp_path / "mod.py"
    _write(target, "def f():\n    # TODO: remove\n    return 1\n")

    violations = run_gate([target], tmp_path / "allow.txt")
    assert any(v.code == "NO_STUB_TODO" for v in violations)


def test_no_stub_gate_detects_pass_only(tmp_path: Path) -> None:
    target = tmp_path / "mod.py"
    _write(target, "def f():\n    pass\n")

    violations = run_gate([target], tmp_path / "allow.txt")
    assert any(v.code == "NO_STUB_PASS_ONLY" for v in violations)


def test_no_stub_gate_detects_ok_true_literal(tmp_path: Path) -> None:
    target = tmp_path / "mod.py"
    _write(target, "def f():\n    return {'ok': True}\n")

    violations = run_gate([target], tmp_path / "allow.txt")
    codes = {v.code for v in violations}
    assert "NO_STUB_OK_TRUE_RESPONSE" in codes
    assert "NO_STUB_OK_TRUE_LITERAL" in codes


def test_no_stub_gate_allowlist_suppresses_violation(tmp_path: Path) -> None:
    target = tmp_path / "pkg" / "mod.py"
    _write(target, "def f(x):\n    # FIXME: tolerated for migration\n    return x\n")

    allow = tmp_path / "allow.txt"
    _write(allow, "*/mod.py|NO_STUB_TODO|2|migration transition\n")

    violations = run_gate([tmp_path / "pkg"], allow)
    assert not violations


def test_no_stub_gate_requires_allow_reason(tmp_path: Path) -> None:
    target = tmp_path / "pkg" / "mod.py"
    _write(target, "def f():\n    return None\n")
    allow = tmp_path / "allow.txt"
    _write(allow, "*/mod.py|NO_STUB_RETURN_NONE_ONLY|2|\n")

    try:
        run_gate([target], allow)
    except ValueError as exc:
        assert "reason missing" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for missing allowlist reason")
