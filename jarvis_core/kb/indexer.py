"""Run artifact -> knowledge base ingestion."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

from .citations import format_evidence_items
from .dedup import dedup_claims
from .merger import merge_sections
from .normalizer import TermNormalizer
from .quality_tags import assign_quality_tags
from .schema import format_front_matter, parse_front_matter
from .topic_router import TopicRouter

AUTO_CLAIMS_START = "<!-- AUTO-CLAIMS-START -->"
AUTO_CLAIMS_END = "<!-- AUTO-CLAIMS-END -->"
AUTO_TOPIC_START = "<!-- AUTO-TOPIC-START -->"
AUTO_TOPIC_END = "<!-- AUTO-TOPIC-END -->"
AUTO_EVIDENCE_START = "<!-- AUTO-EVIDENCE-START -->"
AUTO_EVIDENCE_END = "<!-- AUTO-EVIDENCE-END -->"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _gather_claims(run_dir: Path) -> list[dict]:
    claims: list[dict] = []
    direct = run_dir / "claims.jsonl"
    if direct.exists():
        claims.extend(_load_jsonl(direct))
    claims_dir = run_dir / "claims"
    if claims_dir.exists():
        for path in sorted(claims_dir.glob("*.jsonl")):
            claims.extend(_load_jsonl(path))
    return claims


def _gather_papers(run_dir: Path) -> list[dict]:
    rank_path = run_dir / "research_rank.json"
    if rank_path.exists():
        data = _load_json(rank_path)
        if isinstance(data, dict):
            return data.get("papers") or data.get("results") or []
    for name in ["canonical_papers.jsonl", "papers.jsonl"]:
        path = run_dir / name
        if path.exists():
            return _load_jsonl(path)
    return []


def _normalize_pmid(paper: Mapping) -> str:
    pmid = paper.get("pmid") or paper.get("PMID") or ""
    if pmid:
        return str(pmid)
    paper_id = paper.get("paper_id") or paper.get("paperId") or ""
    if isinstance(paper_id, str) and paper_id.lower().startswith("pmid:"):
        return paper_id.split(":", 1)[1]
    return str(paper_id) if paper_id else "unknown"


def _paper_tags(paper: Mapping) -> list[str]:
    tags = paper.get("tags") or paper.get("keywords") or []
    if isinstance(tags, str):
        tags = [item.strip() for item in tags.split(",") if item.strip()]
    return [str(tag) for tag in tags]


def _build_claim_markdown(claims: Iterable[Mapping]) -> str:
    blocks = []
    for idx, claim in enumerate(claims, start=1):
        quality = assign_quality_tags(claim)
        evidence_text = format_evidence_items(claim.get("evidence") or [])
        note = quality.get("note") or ""
        note_line = f"- 注記: {note}" if note else "- 注記: "
        blocks.append(
            "\n".join(
                [
                    f"## Claim {idx}",
                    f"- 主張: {claim.get('claim_text') or claim.get('claim') or ''}",
                    f"- 根拠: {evidence_text}",
                    f"- 確度: {quality.get('evidence_strength')}",
                    note_line,
                ]
            )
        )
    return "\n\n".join(blocks) if blocks else "- 重要claimは未抽出"


def _ensure_kb_dirs(kb_root: Path) -> None:
    (kb_root / "notes" / "papers").mkdir(parents=True, exist_ok=True)
    (kb_root / "notes" / "topics").mkdir(parents=True, exist_ok=True)
    (kb_root / "notes" / "runs").mkdir(parents=True, exist_ok=True)
    (kb_root / "dict").mkdir(parents=True, exist_ok=True)


def _render_paper_note(front: dict, body: str) -> str:
    return f"{format_front_matter(front)}\n\n{body.strip()}\n"


def _base_paper_body(summary: str) -> str:
    return (
        "# 要約（300〜500字）\n"
        f"{summary}\n\n"
        "# 重要claim（根拠付き）\n"
        f"{AUTO_CLAIMS_START}\n"
        "- 重要claimは未抽出\n"
        f"{AUTO_CLAIMS_END}\n\n"
        "# 自分の研究への接続\n"
        "- 使いどころ:\n"
        "- 次に読むべき:\n"
    )


def _base_topic_body(topic: str) -> str:
    return (
        f"# {topic}：今週の更新\n"
        f"{AUTO_TOPIC_START}\n"
        "- 新規の高確度ポイント（S/A Tier）\n"
        "- 争点（論文間で矛盾）\n"
        "- 未確定（追加調査が必要）\n"
        f"{AUTO_TOPIC_END}\n\n"
        "# エビデンス・マップ\n"
        f"{AUTO_EVIDENCE_START}\n"
        "- Claim → supporting papers（PMIDリンク）\n"
        f"{AUTO_EVIDENCE_END}\n"
    )


def ingest_run(run_dir: Path, kb_root: Path = Path("data/kb"), run_id: str | None = None) -> dict:
    """Ingest run artifacts into KB."""
    run_id = run_id or run_dir.name
    _ensure_kb_dirs(kb_root)

    normalizer = TermNormalizer(kb_root / "dict" / "synonyms.json")
    router = TopicRouter(normalizer)

    papers = _gather_papers(run_dir)
    claims = _gather_claims(run_dir)
    claims = dedup_claims(claims)

    claims_by_paper: dict[str, list[dict]] = {}
    for claim in claims:
        paper_id = claim.get("paper_id") or claim.get("paperId") or claim.get("pmid") or ""
        if not paper_id:
            continue
        claims_by_paper.setdefault(str(paper_id), []).append(claim)

    index_path = kb_root / "index.json"
    index = _load_json(index_path)
    index.setdefault("papers", {})
    index.setdefault("topics", {})
    index.setdefault("runs", {})

    updated_papers = []
    updated_topics = set()

    for paper in papers:
        pmid = _normalize_pmid(paper)
        paper_id = paper.get("paper_id") or paper.get("paperId") or f"PMID:{pmid}"
        title = paper.get("title") or ""
        abstract = paper.get("abstract") or paper.get("summary") or ""
        summary = abstract or "要約は未生成"
        tags = _paper_tags(paper)
        topics = router.classify([title, abstract], tags)

        claim_list = claims_by_paper.get(str(paper_id), []) or claims_by_paper.get(
            f"PMID:{pmid}", []
        )
        claim_markdown = _build_claim_markdown(claim_list)

        paper_note_path = kb_root / "notes" / "papers" / f"PMID_{pmid}.md"
        front_matter = {
            "type": "paper",
            "pmid": pmid,
            "doi": paper.get("doi", ""),
            "title": title,
            "year": paper.get("year"),
            "journal": paper.get("journal", ""),
            "oa": paper.get("oa", paper.get("open_access", "unknown")),
            "tier": paper.get("tier", "C"),
            "score": paper.get("score", 0.0),
            "run_id": run_id,
            "tags": topics or tags,
            "updated_at": _now(),
        }

        if paper_note_path.exists():
            existing = paper_note_path.read_text(encoding="utf-8")
            existing_front, body = parse_front_matter(existing)
            merged_front = {**existing_front, **front_matter}
            body = merge_sections(
                body,
                {
                    "claims": (AUTO_CLAIMS_START, AUTO_CLAIMS_END, claim_markdown),
                },
            )
            note_text = _render_paper_note(merged_front, body)
        else:
            body = _base_paper_body(summary)
            body = merge_sections(
                body,
                {
                    "claims": (AUTO_CLAIMS_START, AUTO_CLAIMS_END, claim_markdown),
                },
            )
            note_text = _render_paper_note(front_matter, body)

        paper_note_path.write_text(note_text, encoding="utf-8")
        updated_papers.append(pmid)

        index["papers"][pmid] = {
            "pmid": pmid,
            "topics": topics,
            "path": str(paper_note_path.relative_to(kb_root)),
            "updated_at": front_matter["updated_at"],
            "run_id": run_id,
            "tier": front_matter["tier"],
        }
        updated_topics.update(topics)

    topic_updates: dict[str, dict] = {}
    for topic in updated_topics:
        topic_note_path = kb_root / "notes" / "topics" / f"{topic}.md"
        summary_lines = [
            "- 新規の高確度ポイント（S/A Tier）",
            "- 争点（論文間で矛盾）",
            "- 未確定（追加調査が必要）",
        ]
        evidence_lines = []
        for pmid in updated_papers:
            evidence_lines.append(f"- {topic} のClaim → PMID_{pmid}")

        body_sections = {
            "topic": (AUTO_TOPIC_START, AUTO_TOPIC_END, "\n".join(summary_lines)),
            "evidence": (
                AUTO_EVIDENCE_START,
                AUTO_EVIDENCE_END,
                (
                    "\n".join(evidence_lines)
                    if evidence_lines
                    else "- Claim → supporting papers（PMIDリンク）"
                ),
            ),
        }

        if topic_note_path.exists():
            existing = topic_note_path.read_text(encoding="utf-8")
            existing_front, body = parse_front_matter(existing)
            merged_front = {**existing_front, "type": "topic", "topic": topic, "updated_at": _now()}
            body = merge_sections(body, body_sections)
            note_text = f"{format_front_matter(merged_front)}\n\n{body.strip()}\n"
        else:
            front = {"type": "topic", "topic": topic, "updated_at": _now()}
            body = _base_topic_body(topic)
            body = merge_sections(body, body_sections)
            note_text = f"{format_front_matter(front)}\n\n{body.strip()}\n"

        topic_note_path.write_text(note_text, encoding="utf-8")
        index["topics"][topic] = {
            "topic": topic,
            "path": str(topic_note_path.relative_to(kb_root)),
            "updated_at": _now(),
        }
        topic_updates[topic] = index["topics"][topic]

    run_note_path = kb_root / "notes" / "runs" / f"RUN_{run_id}_summary.md"
    run_body = (
        f"# Run {run_id} summary\n\n"
        f"- Papers updated: {len(updated_papers)}\n"
        f"- Topics updated: {len(updated_topics)}\n"
    )
    run_note_path.write_text(run_body, encoding="utf-8")

    index["runs"][run_id] = {
        "run_id": run_id,
        "papers": updated_papers,
        "topics": sorted(updated_topics),
        "updated_at": _now(),
        "path": str(run_note_path.relative_to(kb_root)),
    }

    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "papers": updated_papers,
        "topics": sorted(updated_topics),
        "run_id": run_id,
    }
