"""
JARVIS Security & Compliance

M6: セキュリティ・コンプライアンスモジュール
- アクセス制御（RBAC）
- 監査ログ
- GDPR対応（削除・匿名化）
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Role(Enum):
    """ユーザーロール."""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    READONLY = "readonly"


class Permission(Enum):
    """パーミッション."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


# ロールごとのパーミッション
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE, Permission.ADMIN},
    Role.RESEARCHER: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
    Role.REVIEWER: {Permission.READ, Permission.EXECUTE},
    Role.READONLY: {Permission.READ},
}


@dataclass
class AccessLogEntry:
    """アクセスログエントリ."""
    timestamp: str
    user_id: str
    action: str
    resource: str
    granted: bool
    details: dict[str, Any] = field(default_factory=dict)


class AccessControl:
    """アクセス制御."""

    def __init__(self, audit_path: str = "audit/access_log.jsonl"):
        """
        初期化.
        
        Args:
            audit_path: 監査ログパス
        """
        self.audit_path = Path(audit_path)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self._user_roles: dict[str, Role] = {}

    def set_user_role(self, user_id: str, role: Role):
        """ユーザーロールを設定."""
        self._user_roles[user_id] = role
        self._log_access(user_id, "role_assigned", f"role:{role.value}", True)

    def get_user_role(self, user_id: str) -> Role:
        """ユーザーロールを取得."""
        return self._user_roles.get(user_id, Role.READONLY)

    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: str = ""
    ) -> bool:
        """
        パーミッションをチェック.
        
        Args:
            user_id: ユーザーID
            permission: 必要なパーミッション
            resource: リソース名
        
        Returns:
            許可されているか
        """
        role = self.get_user_role(user_id)
        permissions = ROLE_PERMISSIONS.get(role, set())
        granted = permission in permissions

        self._log_access(user_id, permission.value, resource, granted)

        return granted

    def _log_access(
        self,
        user_id: str,
        action: str,
        resource: str,
        granted: bool
    ):
        """アクセスをログ."""
        entry = AccessLogEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            action=action,
            resource=resource,
            granted=granted
        )

        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + '\n')


@dataclass
class DeletionRequest:
    """削除リクエスト."""
    request_id: str
    requester: str
    target_type: str  # user, document, claim
    target_id: str
    reason: str
    requested_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    status: str = "pending"  # pending, approved, completed, rejected


class GDPRCompliance:
    """GDPR対応."""

    # 個人情報パターン
    PII_PATTERNS = [
        (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 'name'),  # 人名
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'phone'),  # 電話番号
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email'),  # メール
    ]

    def __init__(self, requests_path: str = "audit/gdpr_requests.jsonl"):
        """
        初期化.
        
        Args:
            requests_path: リクエストログパス
        """
        self.requests_path = Path(requests_path)
        self.requests_path.parent.mkdir(parents=True, exist_ok=True)
        self._request_counter = 0

    def detect_pii(self, text: str) -> list[dict[str, Any]]:
        """
        PIIを検出.
        
        Args:
            text: 検査対象テキスト
        
        Returns:
            検出されたPIIリスト
        """
        findings = []

        for pattern, pii_type in self.PII_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "value_hash": hashlib.sha256(match.encode()).hexdigest()[:8],
                    "location": text.find(match)
                })

        return findings

    def anonymize_text(self, text: str) -> str:
        """
        テキストを匿名化.
        
        Args:
            text: 匿名化対象テキスト
        
        Returns:
            匿名化されたテキスト
        """
        anonymized = text

        for pattern, pii_type in self.PII_PATTERNS:
            anonymized = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', anonymized)

        return anonymized

    def create_deletion_request(
        self,
        requester: str,
        target_type: str,
        target_id: str,
        reason: str
    ) -> DeletionRequest:
        """
        削除リクエストを作成.
        
        Args:
            requester: リクエスター
            target_type: 対象タイプ
            target_id: 対象ID
            reason: 理由
        
        Returns:
            削除リクエスト
        """
        self._request_counter += 1

        request = DeletionRequest(
            request_id=f"GDPR-{self._request_counter:04d}",
            requester=requester,
            target_type=target_type,
            target_id=target_id,
            reason=reason
        )

        with open(self.requests_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(request), ensure_ascii=False) + '\n')

        logger.info(f"GDPR deletion request created: {request.request_id}")

        return request

    def process_deletion_request(
        self,
        request_id: str,
        approved: bool,
        processor: str
    ) -> bool:
        """
        削除リクエストを処理.
        
        Args:
            request_id: リクエストID
            approved: 承認されたか
            processor: 処理者
        
        Returns:
            処理成功したか
        """
        # 実際の実装では、対象データを削除/匿名化
        status = "completed" if approved else "rejected"

        completion_entry = {
            "request_id": request_id,
            "status": status,
            "processor": processor,
            "completed_at": datetime.now().isoformat()
        }

        with open(self.requests_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(completion_entry, ensure_ascii=False) + '\n')

        return True


# グローバルインスタンス
_access_control: AccessControl | None = None
_gdpr: GDPRCompliance | None = None


def get_access_control() -> AccessControl:
    """アクセス制御を取得."""
    global _access_control
    if _access_control is None:
        _access_control = AccessControl()
    return _access_control


def get_gdpr_compliance() -> GDPRCompliance:
    """GDPR対応を取得."""
    global _gdpr
    if _gdpr is None:
        _gdpr = GDPRCompliance()
    return _gdpr
