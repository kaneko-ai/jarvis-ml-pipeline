"""Weekly learning pack generation."""
from __future__ import annotations

import json
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .schema import parse_front_matter


@dataclass
class PackFile:
    path: Path
    arcname: str


def _iso_week_label(dt: datetime) -> str:
    year, week, _ = dt.isocalendar()
    return f"{year}-{week:02d}"


def _load_index(kb_root: Path) -> dict:
    index_path = kb_root / "index.json"
    if not index_path.exists():
        return {}
    try:
        with open(index_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _note_updated_within(path: Path, start: datetime, end: datetime) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    front, _ = parse_front_matter(content)
    updated_at = front.get("updated_at")
    if updated_at:
        try:
            updated = datetime.fromisoformat(updated_at)
        except ValueError:
            updated = None
    else:
        updated = None
    if updated is None:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        updated = mtime
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return start <= updated <= end


def _collect_week_notes(kb_root: Path, start: datetime, end: datetime, topics: Iterable[str] | None = None) -> list[PackFile]:
    notes: list[PackFile] = []
    papers_dir = kb_root / "notes" / "papers"
    topics_dir = kb_root / "notes" / "topics"

    if papers_dir.exists():
        for path in papers_dir.glob("*.md"):
            if _note_updated_within(path, start, end):
                notes.append(PackFile(path=path, arcname=f"notes/papers/{path.name}"))

    if topics_dir.exists():
        selected_topics = {t.lower() for t in topics} if topics else None
        for path in topics_dir.glob("*.md"):
            if selected_topics and path.stem.lower() not in selected_topics:
                continue
            notes.append(PackFile(path=path, arcname=f"notes/topics/{path.name}"))
    return notes


def _build_readme(week_label: str, notes: list[PackFile]) -> str:
    note_list = "\n".join(f"- {file.arcname}" for file in notes) or "- 対象ノートなし"
    return f"""# Weekly Learning Pack ({week_label})

## 今週のトップ3論点
- 主要論点1（要更新）
- 主要論点2（要更新）
- 主要論点3（要更新）

## 次週の宿題（読むべき論文）
- TODO: 次に読むべき論文を追加

## 矛盾点一覧
- TODO: 矛盾する主張を整理

## 収録ノート
{note_list}

## Podcast化の指示
- このパック全体を教材として、10分のポッドキャスト概要を作成する
- 新規知見と未確定事項を明確に分けて話す
- エビデンスへの参照（PMID/Claim）を明示する
"""


def _build_notebooklm_prompt(week_label: str) -> str:
    return (
        "NotebookLM向けの学習パックです。\n"
        f"週次: {week_label}\n"
        "以下のノートから、最新の高確度ポイント、争点、未確定事項を整理してください。\n"
        "各主張には対応するPMIDとエビデンスを必ず含めてください。\n"
    )


def generate_weekly_pack(
    kb_root: Path = Path("data/kb"),
    packs_root: Path = Path("data/packs/weekly"),
    now: datetime | None = None,
    topics: Iterable[str] | None = None,
) -> Path:
    now = now or datetime.now(timezone.utc)
    week_label = _iso_week_label(now)
    week_start = datetime.fromisocalendar(now.isocalendar().year, now.isocalendar().week, 1).replace(tzinfo=timezone.utc)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    pack_dir = packs_root / week_label
    pack_dir.mkdir(parents=True, exist_ok=True)

    notes = _collect_week_notes(kb_root, week_start, week_end, topics=topics)

    readme_path = pack_dir / "README.md"
    readme_path.write_text(_build_readme(week_label, notes), encoding="utf-8")

    prompt_path = pack_dir / "notebooklm_prompt.txt"
    prompt_path.write_text(_build_notebooklm_prompt(week_label), encoding="utf-8")

    pack_path = pack_dir / "weekly_pack.zip"
    with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(readme_path, arcname="README.md")
        zf.write(prompt_path, arcname="notebooklm_prompt.txt")
        for file in notes:
            zf.write(file.path, arcname=file.arcname)

    metadata = {
        "week": week_label,
        "generated_at": now.isoformat(),
        "notes": [file.arcname for file in notes],
    }
    (pack_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    return pack_path
