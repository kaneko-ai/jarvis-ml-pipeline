"""
JARVIS Dataset Governance

M5: 科学的妥当性のためのデータセット管理
- 学習データの版管理
- ノイズ教師の除外
- 破棄ログ
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class DatasetManifest:
    """データセットマニフェスト."""

    name: str
    version: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    schema_version: str = "1.0"
    pipeline_version: str = "unknown"

    # 統計
    total_records: int = 0
    valid_records: int = 0
    excluded_records: int = 0

    # 品質
    avg_quality_score: float = 0.0
    min_quality_threshold: float = 0.5

    # メタデータ
    description: str = ""
    source_pipelines: list[str] = field(default_factory=list)
    exclusion_reasons: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetManifest:
        """辞書から生成."""
        return cls(**data)


@dataclass
class ExclusionRecord:
    """除外レコード."""

    record_hash: str
    reason: str
    excluded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)


class DatasetGovernance:
    """データセットガバナンス."""

    def __init__(self, datasets_dir: str = "datasets/pretrain"):
        """
        初期化.

        Args:
            datasets_dir: データセットディレクトリ
        """
        self.datasets_dir = Path(datasets_dir)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self._exclusion_hashes: set[str] = set()
        self._load_exclusions()

    def _load_exclusions(self):
        """除外リストを読み込み."""
        exclusion_path = self.datasets_dir / "exclusions.jsonl"
        if exclusion_path.exists():
            with open(exclusion_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        self._exclusion_hashes.add(record.get("record_hash", ""))

    def get_manifest(self, dataset_name: str) -> DatasetManifest | None:
        """
        マニフェストを取得.

        Args:
            dataset_name: データセット名

        Returns:
            マニフェスト
        """
        manifest_path = self.datasets_dir / f"{dataset_name}_manifest.json"
        if not manifest_path.exists():
            return None

        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
        return DatasetManifest.from_dict(data)

    def save_manifest(self, manifest: DatasetManifest):
        """マニフェストを保存."""
        manifest_path = self.datasets_dir / f"{manifest.name}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, ensure_ascii=False, indent=2)

    def compute_record_hash(self, record: dict[str, Any]) -> str:
        """
        レコードのハッシュを計算.

        Args:
            record: レコード

        Returns:
            ハッシュ値
        """
        # 安定したハッシュのため、ソート済みJSONを使用
        content = json.dumps(record, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_excluded(self, record_hash: str) -> bool:
        """除外済みかどうか."""
        return record_hash in self._exclusion_hashes

    def exclude_record(
        self, record: dict[str, Any], reason: str, details: dict[str, Any] | None = None
    ):
        """
        レコードを除外リストに追加.

        Args:
            record: 除外するレコード
            reason: 除外理由
            details: 詳細情報
        """
        record_hash = self.compute_record_hash(record)

        if record_hash in self._exclusion_hashes:
            return  # 既に除外済み

        exclusion = ExclusionRecord(record_hash=record_hash, reason=reason, details=details or {})

        exclusion_path = self.datasets_dir / "exclusions.jsonl"
        with open(exclusion_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(exclusion), ensure_ascii=False) + "\n")

        self._exclusion_hashes.add(record_hash)

    def validate_record(self, record: dict[str, Any], min_quality: float = 0.5) -> tuple[bool, str]:
        """
        レコードを検証.

        Args:
            record: 検証するレコード
            min_quality: 最小品質スコア

        Returns:
            (有効かどうか, 理由)
        """
        record_hash = self.compute_record_hash(record)

        # 除外リストチェック
        if self.is_excluded(record_hash):
            return False, "Previously excluded"

        # 品質チェック
        quality_score = record.get("quality_score", record.get("match_score", {}).get("total", 0))
        if quality_score < min_quality:
            return False, f"Quality below threshold: {quality_score} < {min_quality}"

        # 必須フィールドチェック
        required_fields = ["input", "output"]
        for f_name in required_fields:
            if f_name not in record:
                return False, f"Missing required field: {f_name}"

        return True, "Valid"

    def append_to_dataset(
        self, dataset_name: str, records: list[dict[str, Any]], pipeline_version: str = "unknown"
    ) -> dict[str, int]:
        """
        データセットにレコードを追加.

        Args:
            dataset_name: データセット名
            records: 追加するレコード
            pipeline_version: パイプラインバージョン

        Returns:
            統計（added, excluded, duplicate）
        """
        stats = {"added": 0, "excluded": 0, "duplicate": 0}

        # 既存のマニフェストまたは新規作成
        manifest = self.get_manifest(dataset_name)
        if manifest is None:
            manifest = DatasetManifest(
                name=dataset_name, version="1.0.0", pipeline_version=pipeline_version
            )

        # 既存のハッシュを収集
        dataset_path = self.datasets_dir / f"{dataset_name}.jsonl"
        existing_hashes: set[str] = set()

        if dataset_path.exists():
            with open(dataset_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        existing_record = json.loads(line)
                        existing_hashes.add(self.compute_record_hash(existing_record))

        # レコードを追加
        with open(dataset_path, "a", encoding="utf-8") as f:
            for record in records:
                record_hash = self.compute_record_hash(record)

                # 重複チェック
                if record_hash in existing_hashes:
                    stats["duplicate"] += 1
                    continue

                # 検証
                valid, reason = self.validate_record(record)
                if not valid:
                    stats["excluded"] += 1
                    manifest.exclusion_reasons[reason] = (
                        manifest.exclusion_reasons.get(reason, 0) + 1
                    )
                    continue

                # 追加
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                existing_hashes.add(record_hash)
                stats["added"] += 1

        # マニフェスト更新
        manifest.total_records += stats["added"] + stats["excluded"]
        manifest.valid_records += stats["added"]
        manifest.excluded_records += stats["excluded"]

        self.save_manifest(manifest)

        return stats


# グローバルインスタンス
_governance: DatasetGovernance | None = None


def get_dataset_governance(datasets_dir: str = "datasets/pretrain") -> DatasetGovernance:
    """データセットガバナンスを取得."""
    global _governance
    if _governance is None:
        _governance = DatasetGovernance(datasets_dir)
    return _governance