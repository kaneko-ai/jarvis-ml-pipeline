from unittest.mock import MagicMock, patch
import jarvis_core.cli as cli


def test_main_invokes_run_jarvis_and_prints(monkeypatch, capsys):
    calls = []

    def fake_run_jarvis(goal: str) -> str:
        calls.append(goal)
        return "FAKE_ANSWER"

    monkeypatch.setattr(cli, "run_jarvis", fake_run_jarvis)

    exit_code = cli.main(["test goal"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls == ["test goal"]
    assert "FAKE_ANSWER" in captured.out
