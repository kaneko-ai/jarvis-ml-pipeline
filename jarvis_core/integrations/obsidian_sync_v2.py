"""
JARVIS Obsidian Sync

10. Obsidian連携: 研究ノートへの自動同期
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """同期結果."""

    status: str  # created, updated, unchanged, error
    path: str
    message: str


class ObsidianSync:
    """Obsidian同期.

    研究ノートをObsidian vaultに自動同期
    """

    PAPER_TEMPLATE = """---
title: "{title}"
authors: {authors}
year: {year}
source: {source}
paper_id: {paper_id}
created: {created}
tags: {tags}
---

# {title}

## Metadata
- **Authors**: {authors_str}
- **Year**: {year}
- **Source**: {source}
- **ID**: {paper_id}

## Abstract
{abstract}

## Key Claims
{claims}

## Evidence
{evidence}

## Notes
(Add your notes here)

## Related Papers
{related}
"""

    RUN_TEMPLATE = """---
run_id: "{run_id}"
query: "{query}"
created: {created}
papers_count: {papers_count}
---

# Research Run: {query}

## Overview
- **Run ID**: {run_id}
- **Date**: {created}
- **Papers**: {papers_count}
- **Claims**: {claims_count}

## Papers
{papers_list}

## Key Findings
{findings}

## Summary
{summary}
"""

    def __init__(self, vault_path: str):
        """初期化.

        Args:
            vault_path: Obsidian vaultのパス
        """
        self.vault_path = Path(vault_path)
        self.papers_dir = self.vault_path / "Papers"
        self.runs_dir = self.vault_path / "Runs"

        # ディレクトリ作成
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def sync_paper(
        self,
        paper: dict[str, Any],
        claims: list[dict[str, Any]] | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> SyncResult:
        """論文ノートを同期.

        Args:
            paper: 論文データ
            claims: 関連する主張
            evidence: 関連する根拠

        Returns:
            同期結果
        """
        paper_id = paper.get("paper_id", "unknown")
        title = paper.get("title", "Untitled")

        # ファイル名を安全にする
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        filename = f"{paper_id}_{safe_title}.md"
        filepath = self.papers_dir / filename

        # コンテンツを生成
        claims_md = self._format_claims(claims, paper_id)
        evidence_md = self._format_evidence(evidence, paper_id)

        content = self.PAPER_TEMPLATE.format(
            title=title,
            authors=json.dumps(paper.get("authors", [])),
            year=paper.get("year", "Unknown"),
            source=paper.get("source", "Unknown"),
            paper_id=paper_id,
            created=datetime.now().isoformat(),
            tags=f"[paper, {paper.get('source', 'unknown')}]",
            authors_str=", ".join(paper.get("authors", [])[:3]),
            abstract=paper.get("abstract", "No abstract available."),
            claims=claims_md,
            evidence=evidence_md,
            related="(Add related papers here)",
        )

        return self._write_note(filepath, content)

    def sync_run(
        self,
        run_id: str,
        query: str,
        papers: list[dict[str, Any]],
        claims: list[dict[str, Any]] | None = None,
        summary: str = "",
    ) -> SyncResult:
        """実行ノートを同期.

        Args:
            run_id: 実行ID
            query: 検索クエリ
            papers: 論文リスト
            claims: 主張リスト
            summary: サマリー

        Returns:
            同期結果
        """
        filename = f"{run_id}.md"
        filepath = self.runs_dir / filename

        # 論文リスト
        papers_list = ""
        for paper in papers[:20]:
            paper_id = paper.get("paper_id", "")
            title = paper.get("title", "")
            papers_list += f"- [[{paper_id}]] - {title}\n"

        # 主要な発見
        findings = ""
        if claims:
            for claim in claims[:10]:
                findings += f"- {claim.get('claim_text', '')[:100]}\n"

        content = self.RUN_TEMPLATE.format(
            run_id=run_id,
            query=query,
            created=datetime.now().isoformat(),
            papers_count=len(papers),
            claims_count=len(claims) if claims else 0,
            papers_list=papers_list,
            findings=findings or "No key findings extracted.",
            summary=summary or "No summary generated.",
        )

        return self._write_note(filepath, content)

    def _write_note(self, filepath: Path, content: str) -> SyncResult:
        """ノートを書き込み."""
        try:
            # 既存ファイルをチェック
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    existing = f.read()

                # ハッシュで変更をチェック
                if (
                    hashlib.md5(existing.encode()).hexdigest()
                    == hashlib.md5(content.encode()).hexdigest()
                ):
                    return SyncResult("unchanged", str(filepath), "No changes")

                # 更新
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"Updated note: {filepath}")
                return SyncResult("updated", str(filepath), "Note updated")

            else:
                # 新規作成
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"Created note: {filepath}")
                return SyncResult("created", str(filepath), "Note created")

        except Exception as e:
            logger.error(f"Failed to write note: {e}")
            return SyncResult("error", str(filepath), str(e))

    def _format_claims(
        self,
        claims: list[dict[str, Any]] | None,
        paper_id: str,
    ) -> str:
        """主張をフォーマット."""
        if not claims:
            return "No claims extracted."

        paper_claims = [c for c in claims if c.get("paper_id") == paper_id]

        if not paper_claims:
            return "No claims extracted."

        lines = []
        for claim in paper_claims[:10]:
            claim_type = claim.get("claim_type", "unknown")
            claim_text = claim.get("claim_text", "")
            lines.append(f"- **[{claim_type}]** {claim_text}")

        return "\n".join(lines)

    def _format_evidence(
        self,
        evidence: list[dict[str, Any]] | None,
        paper_id: str,
    ) -> str:
        """根拠をフォーマット."""
        if not evidence:
            return "No evidence linked."

        paper_evidence = [e for e in evidence if e.get("paper_id") == paper_id]

        if not paper_evidence:
            return "No evidence linked."

        lines = []
        for ev in paper_evidence[:10]:
            source = ev.get("source", "unknown")
            text = ev.get("evidence_text", "")[:200]
            lines.append(f"- [{source}] {text}...")

        return "\n".join(lines)

    def get_sync_stats(self) -> dict[str, int]:
        """同期統計を取得."""
        papers_count = len(list(self.papers_dir.glob("*.md")))
        runs_count = len(list(self.runs_dir.glob("*.md")))

        return {
            "papers_synced": papers_count,
            "runs_synced": runs_count,
            "vault_path": str(self.vault_path),
        }
