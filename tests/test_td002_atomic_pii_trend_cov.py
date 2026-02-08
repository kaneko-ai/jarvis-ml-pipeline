from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis_core.scientific_linter import lint_text
from jarvis_core.security import atomic_io
from jarvis_core.security.pii_scan import PIIScanner
from jarvis_core.spec_lint import lint_spec
from jarvis_core.trend_watcher import watch_trend


def test_atomic_write_json_jsonl_and_bytes(tmp_path: Path) -> None:
    text_path = tmp_path / "plain.txt"
    bytes_path = tmp_path / "bytes.bin"
    json_path = tmp_path / "data.json"
    jsonl_path = tmp_path / "rows.jsonl"

    atomic_io.atomic_write(text_path, "hello")
    atomic_io.atomic_write(bytes_path, b"abc")
    atomic_io.atomic_write_json(json_path, {"ok": True}, indent=None)
    atomic_io.atomic_write_jsonl(jsonl_path, [{"i": 1}, {"i": 2}])

    assert text_path.read_text(encoding="utf-8") == "hello"
    assert bytes_path.read_bytes() == b"abc"
    assert json.loads(json_path.read_text(encoding="utf-8"))["ok"] is True
    rows = [
        json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line
    ]
    assert rows == [{"i": 1}, {"i": 2}]


def test_atomic_write_removes_temp_file_on_replace_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "broken.txt"

    def _boom(src: str, dst: str | Path) -> None:  # noqa: ARG001
        raise OSError("replace failed")

    monkeypatch.setattr(atomic_io.os, "replace", _boom)

    with pytest.raises(OSError, match="replace failed"):
        atomic_io.atomic_write(target, "x")

    assert list(tmp_path.glob(".broken.txt.tmp-*.tmp")) == []


def test_pii_summary_and_has_pii() -> None:
    scanner = PIIScanner()
    text = "mail me at user@example.com, backup user@example.com, SSN 123-45-6789"

    summary = scanner.get_pii_summary(text)

    assert summary["has_pii"] is True
    assert summary["total_matches"] >= 3
    assert summary["by_type"]["email"] >= 2
    assert summary["by_type"]["ssn"] >= 1
    assert scanner.has_pii(text) is True
    assert scanner.has_pii("just plain words") is False


def test_watch_trend_and_lint_helpers() -> None:
    assert watch_trend([1.0]).direction == "flat"
    assert watch_trend([1.0, 2.0]).direction == "up"
    assert watch_trend([2.0, 1.0]).direction == "down"
    assert watch_trend([2.0, 2.0]).direction == "flat"

    assert lint_text("clean text").issues == []
    assert lint_spec("clean spec").issues == []
