from __future__ import annotations

from pathlib import Path

from scripts.no_stub_gate import run_gate


def test_no_stub_policy_detects_todo_and_pass(tmp_path: Path):
    target = tmp_path / "stub.py"
    target.write_text(
        "def foo():\n"
        "    # TODO: implement\n"
        "    pass\n",
        encoding="utf-8",
    )
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("", encoding="utf-8")
    violations = run_gate([target], allowlist)
    codes = {v.code for v in violations}
    assert "NO_STUB_TODO" in codes
    assert "NO_STUB_PASS_ONLY" in codes

