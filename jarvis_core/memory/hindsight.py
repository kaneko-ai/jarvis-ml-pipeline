"""
JARVIS Hindsight Memory

最重要: World / Experience / Observation / Opinion の分離
禁止: OpinionがWorldに混入すること
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """メモリタイプ."""

    WORLD = "world"  # 検証済み事実
    EXPERIENCE = "experience"  # 実行・失敗・手動判断
    OBSERVATION = "observation"  # 未検証メモ
    OPINION = "opinion"  # 好み・仮説（隔離）


@dataclass
class MemoryEntry:
    """メモリエントリ."""

    id: str
    memory_type: MemoryType
    content: str
    source: str  # 情報源
    evidence: list[str] = field(default_factory=list)  # 根拠
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str | None = None
    verified: bool = False  # 検証済みフラグ
    verification_method: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "id": self.id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "source": self.source,
            "evidence": self.evidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "verified": self.verified,
            "verification_method": self.verification_method,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryEntry:
        """辞書から生成."""
        return cls(
            id=data["id"],
            memory_type=MemoryType(data["memory_type"]),
            content=data["content"],
            source=data["source"],
            evidence=data.get("evidence", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at"),
            verified=data.get("verified", False),
            verification_method=data.get("verification_method"),
            metadata=data.get("metadata", {}),
        )


class HindsightMemory:
    """Hindsight Memory.

    重要ルール:
    - Opinion は World に昇格させてはならない
    - World には必ず evidence が必要
    - Experience は実行ログとして保存
    """

    def __init__(self, storage_path: str = "data/memory"):
        """
        初期化.

        Args:
            storage_path: ストレージディレクトリ
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._memories: dict[MemoryType, list[MemoryEntry]] = {
            MemoryType.WORLD: [],
            MemoryType.EXPERIENCE: [],
            MemoryType.OBSERVATION: [],
            MemoryType.OPINION: [],
        }

        self._load()

    def _load(self) -> None:
        """ストレージから読み込み."""
        for memory_type in MemoryType:
            file_path = self.storage_path / f"{memory_type.value}.jsonl"
            if file_path.exists():
                with open(file_path, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            entry = MemoryEntry.from_dict(json.loads(line))
                            self._memories[memory_type].append(entry)
                logger.info(
                    f"Loaded {len(self._memories[memory_type])} {memory_type.value} entries"
                )

    def _save(self, memory_type: MemoryType) -> None:
        """ストレージに保存."""
        file_path = self.storage_path / f"{memory_type.value}.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in self._memories[memory_type]:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def add_world(
        self,
        content: str,
        source: str,
        evidence: list[str],
        verification_method: str = "direct_verification",
    ) -> MemoryEntry:
        """
        World（検証済み事実）を追加.

        Args:
            content: 内容
            source: 情報源
            evidence: 根拠（必須）
            verification_method: 検証方法

        Returns:
            MemoryEntry

        Raises:
            ValueError: 根拠がない場合
        """
        if not evidence:
            raise ValueError("World entries require evidence")

        entry = MemoryEntry(
            id=f"world_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            memory_type=MemoryType.WORLD,
            content=content,
            source=source,
            evidence=evidence,
            verified=True,
            verification_method=verification_method,
        )

        self._memories[MemoryType.WORLD].append(entry)
        self._save(MemoryType.WORLD)
        logger.info(f"Added World entry: {entry.id}")

        return entry

    def add_experience(
        self, content: str, source: str, metadata: dict[str, Any] | None = None
    ) -> MemoryEntry:
        """
        Experience（実行・失敗・手動判断）を追加.

        Args:
            content: 内容
            source: 情報源
            metadata: メタデータ

        Returns:
            MemoryEntry
        """
        entry = MemoryEntry(
            id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            memory_type=MemoryType.EXPERIENCE,
            content=content,
            source=source,
            metadata=metadata or {},
        )

        self._memories[MemoryType.EXPERIENCE].append(entry)
        self._save(MemoryType.EXPERIENCE)
        logger.info(f"Added Experience entry: {entry.id}")

        return entry

    def add_observation(self, content: str, source: str) -> MemoryEntry:
        """
        Observation（未検証メモ）を追加.

        Args:
            content: 内容
            source: 情報源

        Returns:
            MemoryEntry
        """
        entry = MemoryEntry(
            id=f"obs_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            memory_type=MemoryType.OBSERVATION,
            content=content,
            source=source,
            verified=False,
        )

        self._memories[MemoryType.OBSERVATION].append(entry)
        self._save(MemoryType.OBSERVATION)
        logger.info(f"Added Observation entry: {entry.id}")

        return entry

    def add_opinion(self, content: str, source: str) -> MemoryEntry:
        """
        Opinion（好み・仮説）を追加.

        注意: Opinionは隔離され、Worldに混入してはならない。

        Args:
            content: 内容
            source: 情報源

        Returns:
            MemoryEntry
        """
        entry = MemoryEntry(
            id=f"opinion_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            memory_type=MemoryType.OPINION,
            content=content,
            source=source,
            verified=False,
        )

        self._memories[MemoryType.OPINION].append(entry)
        self._save(MemoryType.OPINION)
        logger.info(f"Added Opinion entry: {entry.id}")

        return entry

    def promote_to_world(
        self, observation_id: str, evidence: list[str], verification_method: str
    ) -> MemoryEntry | None:
        """
        ObservationをWorldに昇格.

        Args:
            observation_id: Observation ID
            evidence: 根拠（必須）
            verification_method: 検証方法

        Returns:
            新しいWorldエントリ

        Raises:
            ValueError: Opinionを昇格しようとした場合
        """
        # Observationを探す
        obs = None
        for entry in self._memories[MemoryType.OBSERVATION]:
            if entry.id == observation_id:
                obs = entry
                break

        if not obs:
            logger.warning(f"Observation not found: {observation_id}")
            return None

        # 根拠チェック
        if not evidence:
            raise ValueError("Cannot promote to World without evidence")

        # Worldに追加
        world_entry = self.add_world(
            content=obs.content,
            source=obs.source,
            evidence=evidence,
            verification_method=verification_method,
        )

        # Observationを削除
        self._memories[MemoryType.OBSERVATION] = [
            e for e in self._memories[MemoryType.OBSERVATION] if e.id != observation_id
        ]
        self._save(MemoryType.OBSERVATION)

        logger.info(f"Promoted {observation_id} to World: {world_entry.id}")
        return world_entry

    def query(
        self, memory_type: MemoryType | None = None, verified_only: bool = False, limit: int = 100
    ) -> list[MemoryEntry]:
        """
        メモリをクエリ.

        Args:
            memory_type: 特定タイプのみ
            verified_only: 検証済みのみ
            limit: 最大件数

        Returns:
            MemoryEntryリスト
        """
        results = []

        types_to_search = [memory_type] if memory_type else list(MemoryType)

        for mt in types_to_search:
            for entry in self._memories[mt]:
                if verified_only and not entry.verified:
                    continue
                results.append(entry)
                if len(results) >= limit:
                    break

        return results[:limit]