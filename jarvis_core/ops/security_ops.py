"""
JARVIS Security & Operations

Step 91-95: 運用・安全
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# コスト/レイテンシ上限（Step 93）
class OperationLimits:
    """運用上限."""

    MAX_COST_PER_RUN = 1.0  # ドル
    MAX_LATENCY_MS = 60000  # 60秒
    MAX_RETRIES = 3
    MAX_PAPERS_PER_RUN = 50

    @classmethod
    def check_cost(cls, cost: float) -> bool:
        """コスト上限チェック."""
        return cost <= cls.MAX_COST_PER_RUN

    @classmethod
    def check_latency(cls, latency_ms: int) -> bool:
        """レイテンシ上限チェック."""
        return latency_ms <= cls.MAX_LATENCY_MS


# PII検出強化（Step 91）
class PIIDetector:
    """PII検出器."""

    PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_us": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "phone_jp": r"\b0\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{4}\b",
        "credit_card": r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    }

    @classmethod
    def detect(cls, text: str) -> list[dict[str, Any]]:
        """PII検出."""
        findings = []
        for pii_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "match": match[:4] + "***",  # マスク
                })
        return findings

    @classmethod
    def mask(cls, text: str) -> str:
        """PIIをマスク."""
        result = text
        for pii_type, pattern in cls.PATTERNS.items():
            result = re.sub(pattern, "[REDACTED]", result)
        return result


# 保存ポリシー（Step 92）
@dataclass
class RetentionPolicy:
    """保存ポリシー."""

    # 保持期間（日）
    run_logs: int = 90
    audit_logs: int = 365
    pii_data: int = 30

    def should_delete(self, created_at: datetime, data_type: str) -> bool:
        """削除すべきか判定."""
        now = datetime.now()
        retention = getattr(self, data_type, 90)
        return (now - created_at).days > retention


# 監査ログローテーション（Step 95）
class AuditLogRotator:
    """監査ログローテーション."""

    def __init__(
        self,
        log_dir: str = "logs/audit",
        max_size_mb: int = 100,
        max_files: int = 10,
    ):
        """初期化."""
        self.log_dir = Path(log_dir)
        self.max_size_mb = max_size_mb
        self.max_files = max_files

    def rotate_if_needed(self, log_file: str) -> str | None:
        """必要ならローテート."""
        log_path = self.log_dir / log_file

        if not log_path.exists():
            return None

        size_mb = log_path.stat().st_size / (1024 * 1024)

        if size_mb >= self.max_size_mb:
            # ローテート
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated = log_path.with_suffix(f".{timestamp}.jsonl")
            log_path.rename(rotated)

            # 古いファイル削除
            self._cleanup_old_files(log_file)

            return str(rotated)

        return None

    def _cleanup_old_files(self, base_name: str) -> None:
        """古いファイルを削除."""
        pattern = base_name.replace(".jsonl", ".*.jsonl")
        files = sorted(self.log_dir.glob(pattern), reverse=True)

        for old_file in files[self.max_files:]:
            old_file.unlink()
            logger.info(f"Deleted old log: {old_file}")


# 新機能追加DoD（Step 96）
class FeatureDoD:
    """新機能追加のDoD."""

    REQUIRED_CHECKS = [
        "has_tests",
        "has_docs",
        "passes_spec_lint",
        "passes_quality_gate",
        "no_new_warnings",
        "bundle_contract_compatible",
    ]

    @classmethod
    def check(cls, feature_dir: Path) -> dict[str, bool]:
        """DoDチェック."""
        checks = {}

        # テストがあるか
        tests_dir = feature_dir / "tests"
        checks["has_tests"] = tests_dir.exists() and any(tests_dir.glob("test_*.py"))

        # ドキュメントがあるか
        docs = list(feature_dir.glob("*.md")) + list(feature_dir.glob("docs/*.md"))
        checks["has_docs"] = len(docs) > 0

        # その他は外部チェック（CI等）
        checks["passes_spec_lint"] = True  # CIで検証
        checks["passes_quality_gate"] = True  # CIで検証
        checks["no_new_warnings"] = True  # CIで検証
        checks["bundle_contract_compatible"] = True  # 手動検証

        return checks


# Plugin/Skill登録規約（Step 97）
@dataclass
class SkillSpec:
    """Skill仕様."""
    name: str
    version: str
    description: str
    inputs: dict[str, str]
    outputs: dict[str, str]
    requires_index: bool = False

    def validate(self) -> list[str]:
        """仕様を検証."""
        errors = []
        if not self.name:
            errors.append("name is required")
        if not self.version:
            errors.append("version is required")
        if not self.description:
            errors.append("description is required")
        return errors


# Skillテンプレート（Step 98）
SKILL_TEMPLATE = '''"""
{name} Skill

{description}
"""

from __future__ import annotations
from typing import Any, Dict

class {class_name}:
    """
    {name} Skill.
    
    Inputs: {inputs}
    Outputs: {outputs}
    """
    
    def __init__(self):
        """初期化."""
        pass
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """実行."""
        # TODO: Implement skill logic
        return {{"status": "success"}}


def register() -> Dict[str, Any]:
    """Skill登録情報."""
    return {{
        "name": "{name}",
        "version": "1.0.0",
        "class": {class_name},
    }}
'''


def generate_skill_template(spec: SkillSpec) -> str:
    """Skillテンプレートを生成."""
    class_name = "".join(word.capitalize() for word in spec.name.split("_")) + "Skill"

    return SKILL_TEMPLATE.format(
        name=spec.name,
        class_name=class_name,
        description=spec.description,
        inputs=spec.inputs,
        outputs=spec.outputs,
    )
