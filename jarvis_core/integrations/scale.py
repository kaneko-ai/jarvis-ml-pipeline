"""
JARVIS Scale Integrations

Phase9: Zotero/Screenpipe統合（監査ログ付き）
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """監査ログエントリ."""

    timestamp: str
    action: str
    source: str
    target: str
    user: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "source": self.source,
            "target": self.target,
            "user": self.user,
            "details": self.details,
        }


class AuditLog:
    """監査ログ.

    Phase9: すべての外部統合アクションを記録
    """

    def __init__(self, log_path: str = "logs/audit.jsonl"):
        """初期化."""
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        source: str,
        target: str,
        user: str = "system",
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """アクションを記録."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            source=source,
            target=target,
            user=user,
            details=details or {},
        )

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

        logger.info(f"Audit: {action} from {source} to {target}")
        return entry

    def get_entries(self, limit: int = 100) -> list[AuditEntry]:
        """エントリを取得."""
        if not self.log_path.exists():
            return []

        entries = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    entries.append(AuditEntry(**data))

        return entries[-limit:]


class ZoteroIntegration:
    """Zotero連携.

    Phase9: 文献ソースの一元化
    """

    def __init__(self, library_path: str | None = None, audit_log: AuditLog | None = None):
        """初期化."""
        self.library_path = Path(library_path) if library_path else None
        self.audit = audit_log or AuditLog()

    def import_collection(self, collection_name: str) -> list[dict[str, Any]]:
        """コレクションをインポート."""
        self.audit.log(
            action="import_collection",
            source="zotero",
            target=collection_name,
            details={"collection": collection_name},
        )

        # TODO: 実際のZotero API連携
        logger.info(f"Zotero import: {collection_name}")
        return []

    def export_to_collection(
        self,
        papers: list[dict[str, Any]],
        collection_name: str,
    ) -> int:
        """コレクションにエクスポート."""
        self.audit.log(
            action="export_collection",
            source="jarvis",
            target=f"zotero/{collection_name}",
            details={"paper_count": len(papers)},
        )

        logger.info(f"Exported {len(papers)} papers to Zotero:{collection_name}")
        return len(papers)


class ScreenpipeIntegration:
    """Screenpipe連携.

    Phase9: 作業ログの構造化
    """

    def __init__(self, log_dir: str | None = None, audit_log: AuditLog | None = None):
        """初期化."""
        self.log_dir = Path(log_dir) if log_dir else None
        self.audit = audit_log or AuditLog()

    def import_logs(self, date_from: str, date_to: str) -> list[dict[str, Any]]:
        """ログをインポート."""
        self.audit.log(
            action="import_logs",
            source="screenpipe",
            target="jarvis",
            details={"date_from": date_from, "date_to": date_to},
        )

        # TODO: 実際のScreenpipe連携
        logger.info(f"Screenpipe import: {date_from} to {date_to}")
        return []

    def extract_research_context(self, logs: list[dict[str, Any]]) -> dict[str, Any]:
        """研究コンテキストを抽出."""
        # TODO: ログから論文閲覧、キーワード、作業パターンを抽出
        return {
            "keywords": [],
            "papers_viewed": [],
            "work_sessions": [],
        }
