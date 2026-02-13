from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jarvis_core.ingestion.yomitoku_cli import check_yomitoku_available, run_yomitoku_cli


def test_check_yomitoku_available_true():
    with patch("jarvis_core.ingestion.yomitoku_cli.shutil.which", return_value="/usr/bin/yomitoku"):
        assert check_yomitoku_available() is True


def test_check_yomitoku_available_false():
    with patch("jarvis_core.ingestion.yomitoku_cli.shutil.which", return_value=None):
        assert check_yomitoku_available() is False


def test_run_yomitoku_cli_success(tmp_path: Path):
    input_pdf = tmp_path / "paper.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "ocr_out"
    output_dir.mkdir()
    (output_dir / "result.md").write_text("# OCR\ntext", encoding="utf-8")

    mock_completed = Mock(returncode=0, stdout="ok", stderr="")
    with (
        patch("jarvis_core.ingestion.yomitoku_cli.shutil.which", return_value="/usr/bin/yomitoku"),
        patch("jarvis_core.ingestion.yomitoku_cli.subprocess.run", return_value=mock_completed),
    ):
        result = run_yomitoku_cli(input_path=input_pdf, output_dir=output_dir)

    assert result["returncode"] == 0
    assert "text" in result["text"]
    assert result["text_path"] is not None


def test_run_yomitoku_cli_failure_raises(tmp_path: Path):
    input_pdf = tmp_path / "paper.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "ocr_out"

    mock_completed = Mock(returncode=2, stdout="", stderr="error")
    with (
        patch("jarvis_core.ingestion.yomitoku_cli.shutil.which", return_value="/usr/bin/yomitoku"),
        patch("jarvis_core.ingestion.yomitoku_cli.subprocess.run", return_value=mock_completed),
    ):
        with pytest.raises(RuntimeError):
            run_yomitoku_cli(input_path=input_pdf, output_dir=output_dir)
