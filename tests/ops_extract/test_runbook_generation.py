from __future__ import annotations

from pathlib import Path

from jarvis_core.ops_extract.runbook import generate_runbook


def test_runbook_generation(tmp_path: Path):
    lessons = tmp_path / "lessons_learned.md"
    lessons.write_text(
        "# Lessons Learned\n\n"
        "- category: ocr\n"
        "- root_cause: yomitoku missing\n"
        "- block_rule: check_yomitoku_available\n",
        encoding="utf-8",
    )
    out = generate_runbook(lessons_path=lessons, output_path=tmp_path / "runbook.md")
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "ocr" in content
    assert "check_yomitoku_available" in content

