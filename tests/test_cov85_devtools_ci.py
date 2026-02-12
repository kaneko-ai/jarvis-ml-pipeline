from __future__ import annotations

import subprocess
import sys

import pytest

from jarvis_core.devtools import ci


def test_run_test_commands_build_correct_args(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(cmd, **kwargs):  # noqa: ANN001, ANN003
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=7)

    monkeypatch.setattr(ci.subprocess, "run", _fake_run)

    assert ci.run_core_tests(verbose=True) == 7
    assert calls[-1][:4] == [sys.executable, "-m", "pytest", "-m"]
    assert "-v" in calls[-1]

    assert ci.run_legacy_tests(verbose=False) == 7
    assert "-v" not in calls[-1]

    assert ci.run_all_tests(verbose=True) == 7
    assert calls[-1][:3] == [sys.executable, "-m", "pytest"]


def test_check_imports_success_and_failure(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    ok = subprocess.CompletedProcess(["x"], returncode=0, stdout="OK", stderr="")
    ng = subprocess.CompletedProcess(["x"], returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(ci.subprocess, "run", lambda *args, **kwargs: ok)
    assert ci.check_imports() == 0

    monkeypatch.setattr(ci.subprocess, "run", lambda *args, **kwargs: ng)
    assert ci.check_imports() == 1
    captured = capsys.readouterr()
    assert "Import failed" in captured.out


def test_main_command_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ci, "run_core_tests", lambda verbose=True: 11)
    monkeypatch.setattr(ci, "run_legacy_tests", lambda verbose=True: 12)
    monkeypatch.setattr(ci, "run_all_tests", lambda verbose=True: 13)
    monkeypatch.setattr(ci, "check_imports", lambda: 14)

    for argv, expected in [
        (["ci.py", "core-tests", "-q"], 11),
        (["ci.py", "legacy-tests"], 12),
        (["ci.py", "all-tests"], 13),
        (["ci.py", "check-imports"], 14),
        (["ci.py", "full-ci"], 14),
        (["ci.py"], 0),
    ]:
        monkeypatch.setattr(sys, "argv", argv)
        with pytest.raises(SystemExit) as exc:
            ci.main()
        assert exc.value.code == expected
