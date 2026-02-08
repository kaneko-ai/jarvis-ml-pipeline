"""Tests for scripts.validate_bundle."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_bundle import REQUIRED_FILES, validate_bundle


def _create_valid_bundle(path: Path) -> None:
    for filename in REQUIRED_FILES:
        file_path = path / filename
        if filename.endswith(".json"):
            file_path.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
        elif filename.endswith(".jsonl"):
            file_path.write_text(json.dumps({"row": 1}) + "\n", encoding="utf-8")
        else:
            file_path.write_text("# report\n", encoding="utf-8")


def test_validate_bundle_success(tmp_path: Path) -> None:
    _create_valid_bundle(tmp_path)

    is_valid, errors = validate_bundle(tmp_path)

    assert is_valid is True
    assert errors == []


def test_validate_bundle_missing_file(tmp_path: Path) -> None:
    _create_valid_bundle(tmp_path)
    (tmp_path / "claims.jsonl").unlink()

    is_valid, errors = validate_bundle(tmp_path)

    assert is_valid is False
    assert any("claims.jsonl" in message for message in errors)


def test_validate_bundle_empty_file(tmp_path: Path) -> None:
    _create_valid_bundle(tmp_path)
    (tmp_path / "scores.json").write_text("", encoding="utf-8")

    is_valid, errors = validate_bundle(tmp_path)

    assert is_valid is False
    assert any("Empty file: scores.json" in message for message in errors)


def test_validate_bundle_invalid_json(tmp_path: Path) -> None:
    _create_valid_bundle(tmp_path)
    (tmp_path / "scores.json").write_text("{invalid", encoding="utf-8")

    is_valid, errors = validate_bundle(tmp_path)

    assert is_valid is False
    assert any("Invalid JSON in scores.json" in message for message in errors)


def test_validate_bundle_invalid_jsonl(tmp_path: Path) -> None:
    _create_valid_bundle(tmp_path)
    (tmp_path / "papers.jsonl").write_text('{"ok":1}\n{"bad"\n', encoding="utf-8")

    is_valid, errors = validate_bundle(tmp_path)

    assert is_valid is False
    assert any("Invalid JSONL in papers.jsonl" in message for message in errors)


def test_validate_bundle_nonexistent_directory() -> None:
    is_valid, errors = validate_bundle("/nonexistent/path/for/td003")

    assert is_valid is False
    assert errors
