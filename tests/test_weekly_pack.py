import zipfile
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.kb.weekly_pack import generate_weekly_pack


def test_weekly_pack_contains_notes(tmp_path: Path):
    kb_root = tmp_path / "kb"
    papers_dir = kb_root / "notes" / "papers"
    topics_dir = kb_root / "notes" / "topics"
    papers_dir.mkdir(parents=True, exist_ok=True)
    topics_dir.mkdir(parents=True, exist_ok=True)

    paper_note = papers_dir / "PMID_9999.md"
    paper_note.write_text(
        """---
type: paper
pmid: "9999"
updated_at: "2024-01-03T00:00:00+00:00"
---

# Test
""",
        encoding="utf-8",
    )

    topic_note = topics_dir / "cd73.md"
    topic_note.write_text(
        """---
type: topic
topic: cd73
updated_at: "2024-01-03T00:00:00+00:00"
---

# CD73
""",
        encoding="utf-8",
    )

    packs_root = tmp_path / "packs"
    now = datetime(2024, 1, 4, tzinfo=timezone.utc)
    pack_path = generate_weekly_pack(kb_root=kb_root, packs_root=packs_root / "weekly", now=now, topics=["cd73"])

    assert pack_path.exists()
    with zipfile.ZipFile(pack_path, "r") as zf:
        names = set(zf.namelist())
    assert "README.md" in names
    assert "notes/papers/PMID_9999.md" in names
    assert "notes/topics/cd73.md" in names
