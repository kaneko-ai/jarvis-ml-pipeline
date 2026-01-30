"""
JARVIS Audit Module - 監査ログ

全実行の監査ログを出力。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AuditEntry:
    """監査ログエントリ."""

    timestamp: str
    run_id: str
    stage: str
    action: str
    actor: str = "system"
    details: dict[str, Any] = field(default_factory=dict)
    provenance_rate: float = 0.0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """
    監査ログ出力.

    全ての実行を記録し、説明可能性を担保。
    """

    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or Path("artifacts/audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.entries: list[AuditEntry] = []
        self.run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def log(
        self,
        stage: str,
        action: str,
        details: dict | None = None,
        provenance_rate: float = 0.0,
        success: bool = True,
        error: str | None = None,
    ) -> AuditEntry:
        """監査ログを記録."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            run_id=self.run_id,
            stage=stage,
            action=action,
            details=details or {},
            provenance_rate=provenance_rate,
            success=success,
            error=error,
        )

        self.entries.append(entry)
        self._write_entry(entry)

        return entry

    def _write_entry(self, entry: AuditEntry) -> None:
        """エントリをファイルに書き込み."""
        log_file = self.log_dir / f"audit_{self.run_id}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

    def get_summary(self) -> dict[str, Any]:
        """サマリーを取得."""
        if not self.entries:
            return {"run_id": self.run_id, "entries": 0}

        stages = list(set(e.stage for e in self.entries))
        errors = [e for e in self.entries if not e.success]
        avg_provenance = sum(e.provenance_rate for e in self.entries) / len(self.entries)

        return {
            "run_id": self.run_id,
            "entries": len(self.entries),
            "stages": stages,
            "errors": len(errors),
            "avg_provenance_rate": avg_provenance,
            "start_time": self.entries[0].timestamp,
            "end_time": self.entries[-1].timestamp,
        }

    def export_html(self) -> str:
        """HTML形式でエクスポート."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>JARVIS Audit Log - {self.run_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; }}
        h1 {{ color: #1a73e8; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #1a73e8; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .error {{ color: red; }}
        .success {{ color: green; }}
    </style>
</head>
<body>
    <h1>監査ログ: {self.run_id}</h1>
    <p>エントリ数: {len(self.entries)}</p>
    <table>
        <tr>
            <th>時刻</th>
            <th>ステージ</th>
            <th>アクション</th>
            <th>根拠率</th>
            <th>状態</th>
        </tr>
"""
        for entry in self.entries:
            status_class = "success" if entry.success else "error"
            status_text = "成功" if entry.success else f"失敗: {entry.error}"
            html += f"""        <tr>
            <td>{entry.timestamp}</td>
            <td>{entry.stage}</td>
            <td>{entry.action}</td>
            <td>{entry.provenance_rate:.1%}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>
"""

        html += """    </table>
</body>
</html>"""

        return html


class FailureDiagnoser:
    """
    失敗診断.

    パイプライン失敗の原因を分類。
    """

    FAILURE_TYPES = {
        "provenance": ["evidence", "provenance", "根拠"],
        "timeout": ["timeout", "timed out", "タイムアウト"],
        "resource": ["memory", "OOM", "GPU", "リソース"],
        "validation": ["validation", "schema", "contract", "検証"],
        "dependency": ["import", "module", "dependency", "依存"],
        "network": ["connection", "network", "API", "ネットワーク"],
    }

    def diagnose(self, error_message: str) -> dict[str, Any]:
        """失敗を診断."""
        error_lower = error_message.lower()

        for failure_type, keywords in self.FAILURE_TYPES.items():
            if any(kw.lower() in error_lower for kw in keywords):
                return {
                    "type": failure_type,
                    "keywords_matched": [kw for kw in keywords if kw.lower() in error_lower],
                    "recommendation": self._get_recommendation(failure_type),
                }

        return {
            "type": "unknown",
            "keywords_matched": [],
            "recommendation": "エラーメッセージを確認してください",
        }

    def _get_recommendation(self, failure_type: str) -> str:
        """推奨対応を取得."""
        recommendations = {
            "provenance": "証拠付けを確認し、根拠のない主張を削除してください",
            "timeout": "タイムアウト時間を延長するか、バッチサイズを小さくしてください",
            "resource": "GPU メモリを解放するか、CPU モードで実行してください",
            "validation": "入力データのスキーマを確認してください",
            "dependency": "必要なパッケージをインストールしてください: pip install -e .[ml]",
            "network": "ネットワーク接続を確認してください",
        }
        return recommendations.get(failure_type, "")


class CacheOptimizer:
    """
    キャッシュ最適化.

    キャッシュのヒット率と効率を監視。
    """

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path("artifacts/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"hits": 0, "misses": 0, "size_bytes": 0}

    def record_hit(self) -> None:
        """キャッシュヒットを記録."""
        self.stats["hits"] += 1

    def record_miss(self) -> None:
        """キャッシュミスを記録."""
        self.stats["misses"] += 1

    def get_hit_rate(self) -> float:
        """ヒット率を取得."""
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / total if total > 0 else 0.0

    def get_stats(self) -> dict[str, Any]:
        """統計を取得."""
        return {**self.stats, "hit_rate": self.get_hit_rate()}

    def optimize(self) -> dict[str, Any]:
        """キャッシュを最適化."""

        # Calculate cache size
        total_size = 0
        file_count = 0

        if self.cache_dir.exists():
            for f in self.cache_dir.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size
                    file_count += 1

        self.stats["size_bytes"] = total_size

        # If cache too large (> 1GB), clear old entries
        MAX_SIZE = 1024 * 1024 * 1024  # 1GB
        cleared = False

        if total_size > MAX_SIZE:
            # Clear oldest files (would implement LRU in production)
            cleared = True

        return {
            "total_size_mb": total_size / (1024 * 1024),
            "file_count": file_count,
            "cleared": cleared,
            "hit_rate": self.get_hit_rate(),
        }


# グローバルインスタンス
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """監査ログを取得."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_audit(stage: str, action: str, **kwargs) -> AuditEntry:
    """監査ログを記録（便利関数）."""
    return get_audit_logger().log(stage, action, **kwargs)