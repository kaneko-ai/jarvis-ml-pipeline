"""
JARVIS External Integration

M7: 外部ツール連携
- プラグインAPIインターフェース
- Webhook通知
- 外部サービス連携
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class WebhookEvent(Enum):
    """Webhookイベントタイプ."""
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    STAGE_COMPLETED = "stage.completed"
    QUALITY_ALERT = "quality.alert"
    REVIEW_REQUIRED = "review.required"
    DRIFT_DETECTED = "drift.detected"


@dataclass
class WebhookConfig:
    """Webhook設定."""
    webhook_id: str
    url: str
    secret: str
    events: List[WebhookEvent]
    enabled: bool = True
    retry_count: int = 3
    timeout_sec: int = 30


@dataclass
class WebhookPayload:
    """Webhookペイロード."""
    event: WebhookEvent
    run_id: str
    timestamp: str
    data: Dict[str, Any]
    signature: str = ""
    
    def compute_signature(self, secret: str) -> str:
        """署名を計算."""
        payload = json.dumps({
            "event": self.event.value,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "data": self.data
        }, sort_keys=True)
        return hashlib.hmac_new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest() if hasattr(hashlib, 'hmac_new') else hashlib.sha256((secret + payload).encode()).hexdigest()


class WebhookManager:
    """Webhookマネージャー."""
    
    def __init__(self, config_path: str = "configs/webhooks.json"):
        """
        初期化.
        
        Args:
            config_path: 設定ファイルパス
        """
        self.config_path = Path(config_path)
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """設定を読み込み."""
        if not self.config_path.exists():
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for wh in data.get("webhooks", []):
            config = WebhookConfig(
                webhook_id=wh["webhook_id"],
                url=wh["url"],
                secret=wh.get("secret", ""),
                events=[WebhookEvent(e) for e in wh.get("events", [])],
                enabled=wh.get("enabled", True)
            )
            self._webhooks[config.webhook_id] = config
    
    def register_webhook(self, config: WebhookConfig):
        """Webhookを登録."""
        self._webhooks[config.webhook_id] = config
        logger.info(f"Webhook registered: {config.webhook_id}")
    
    def trigger(
        self,
        event: WebhookEvent,
        run_id: str,
        data: Dict[str, Any]
    ) -> List[str]:
        """
        Webhookをトリガー.
        
        Args:
            event: イベントタイプ
            run_id: 実行ID
            data: データ
        
        Returns:
            トリガーされたWebhook IDリスト
        """
        triggered = []
        
        payload = WebhookPayload(
            event=event,
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            data=data
        )
        
        for webhook_id, config in self._webhooks.items():
            if not config.enabled:
                continue
            
            if event not in config.events:
                continue
            
            # 実際の実装ではHTTP POSTを送信
            logger.info(f"Webhook triggered: {webhook_id} for event {event.value}")
            triggered.append(webhook_id)
        
        return triggered


@dataclass
class PluginAPISpec:
    """プラグインAPI仕様."""
    method: str  # GET, POST, etc.
    path: str
    description: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None


class PluginAPIRegistry:
    """プラグインAPIレジストリ."""
    
    def __init__(self):
        """初期化."""
        self._handlers: Dict[str, Callable] = {}
        self._specs: List[PluginAPISpec] = []
    
    def register(
        self,
        method: str,
        path: str,
        handler: Callable,
        description: str = ""
    ):
        """
        APIを登録.
        
        Args:
            method: HTTPメソッド
            path: パス
            handler: ハンドラー関数
            description: 説明
        """
        key = f"{method.upper()}:{path}"
        self._handlers[key] = handler
        self._specs.append(PluginAPISpec(
            method=method.upper(),
            path=path,
            description=description
        ))
        logger.info(f"Plugin API registered: {key}")
    
    def get_handler(self, method: str, path: str) -> Optional[Callable]:
        """ハンドラーを取得."""
        key = f"{method.upper()}:{path}"
        return self._handlers.get(key)
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """OpenAPI仕様を取得."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "JARVIS Plugin API",
                "version": "1.0.0"
            },
            "paths": {
                spec.path: {
                    spec.method.lower(): {
                        "summary": spec.description,
                        "responses": {"200": {"description": "Success"}}
                    }
                }
                for spec in self._specs
            }
        }


class ExternalServiceConnector:
    """外部サービスコネクター."""
    
    def __init__(self):
        """初期化."""
        self._connections: Dict[str, Dict[str, Any]] = {}
    
    def register_service(
        self,
        service_id: str,
        service_type: str,
        config: Dict[str, Any]
    ):
        """
        サービスを登録.
        
        Args:
            service_id: サービスID
            service_type: サービスタイプ（zotero, notion, slack等）
            config: 設定
        """
        self._connections[service_id] = {
            "type": service_type,
            "config": config,
            "status": "registered"
        }
        logger.info(f"External service registered: {service_id} ({service_type})")
    
    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """サービスを取得."""
        return self._connections.get(service_id)
    
    def list_services(self) -> List[str]:
        """登録済みサービスをリスト."""
        return list(self._connections.keys())


# グローバルインスタンス
_webhook_manager: Optional[WebhookManager] = None
_api_registry: Optional[PluginAPIRegistry] = None
_service_connector: Optional[ExternalServiceConnector] = None


def get_webhook_manager() -> WebhookManager:
    """Webhookマネージャーを取得."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


def get_plugin_api_registry() -> PluginAPIRegistry:
    """プラグインAPIレジストリを取得."""
    global _api_registry
    if _api_registry is None:
        _api_registry = PluginAPIRegistry()
    return _api_registry


def get_service_connector() -> ExternalServiceConnector:
    """外部サービスコネクターを取得."""
    global _service_connector
    if _service_connector is None:
        _service_connector = ExternalServiceConnector()
    return _service_connector
