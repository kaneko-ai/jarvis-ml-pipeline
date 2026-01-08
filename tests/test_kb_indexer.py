import json
from pathlib import Path

from jarvis_core.kb.indexer import ingest_run


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_kb_indexer_preserves_manual_sections(tmp_path: Path):
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    papers = [
        {
            "pmid": "1234",
            "title": "CD73 in the TME",
            "abstract": "Adenosine pathway impacts tumor microenvironment.",
            "year": 2024,
            "journal": "Test Journal",
            "oa": "gold",
            "tier": "A",
            "score": 0.9,
        }
    ]
    _write_jsonl(run_dir / "papers.jsonl", papers)

    claims = [
        {
            "paper_id": "PMID:1234",
            "claim_id": "c1",
            "claim_text": "CD73 increases adenosine production.",
            "evidence": [
                {
                    "chunk_id": "chunk-1",
                    "locator": "Results",
                    "quote": "CD73 increased",
                    "score": 0.8,
                }
            ],
        }
    ]
    _write_jsonl(run_dir / "claims.jsonl", claims)

    kb_root = tmp_path / "kb"
    note_path = kb_root / "notes" / "papers" / "PMID_1234.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        """---
"""
        + "type: paper\n"
        + 'pmid: "1234"\n'
        + "---\n\n"
        + "# 自分の研究への接続\n"
        + "- 手書きメモ\n"
        + "<!-- AUTO-CLAIMS-START -->\n"
        + "- 旧いclaim\n"
        + "<!-- AUTO-CLAIMS-END -->\n",
        encoding="utf-8",
    )

    result = ingest_run(run_dir, kb_root=kb_root, run_id="run-1")

    updated = note_path.read_text(encoding="utf-8")
    assert "手書きメモ" in updated
    assert "CD73 increases adenosine production" in updated
    assert result["papers"] == ["1234"]
