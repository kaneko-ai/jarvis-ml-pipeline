"""ITER-09: 運用耐久 (Operational Resilience).

長時間運用での安定性向上。
- リソースモニタリング
- グレースフルシャットダウン
- 自動復旧
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """リソースメトリクス."""
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    disk_free_gb: float = 0.0
    open_files: int = 0
    timestamp: str = ""
    
    def to_dict(self) -> dict:
        return {
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "disk_free_gb": self.disk_free_gb,
            "open_files": self.open_files,
            "timestamp": self.timestamp,
        }


class ResourceMonitor:
    """リソースモニター.
    
    システムリソースを監視し、問題を早期検出。
    """
    
    def __init__(
        self,
        memory_threshold_mb: float = 8000,
        disk_threshold_gb: float = 10,
        check_interval: int = 60,
    ):
        self.memory_threshold = memory_threshold_mb
        self.disk_threshold = disk_threshold_gb
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._alerts: List[Dict[str, Any]] = []
    
    def start(self) -> None:
        """監視開始."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Resource monitor started")
    
    def stop(self) -> None:
        """監視停止."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Resource monitor stopped")
    
    def get_metrics(self) -> ResourceMetrics:
        """現在のメトリクスを取得."""
        metrics = ResourceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        try:
            import psutil
            
            process = psutil.Process()
            metrics.memory_mb = process.memory_info().rss / (1024 * 1024)
            metrics.cpu_percent = process.cpu_percent()
            metrics.open_files = len(process.open_files())
            
            disk = psutil.disk_usage("/")
            metrics.disk_free_gb = disk.free / (1024 ** 3)
        except ImportError:
            # psutilがない場合は基本情報のみ
            pass
        except Exception as e:
            logger.warning(f"Failed to get metrics: {e}")
        
        return metrics
    
    def _monitor_loop(self) -> None:
        """監視ループ."""
        while self._running:
            try:
                metrics = self.get_metrics()
                
                # メモリ警告
                if metrics.memory_mb > self.memory_threshold:
                    self._add_alert("HIGH_MEMORY", f"Memory: {metrics.memory_mb:.0f}MB")
                
                # ディスク警告
                if metrics.disk_free_gb < self.disk_threshold:
                    self._add_alert("LOW_DISK", f"Disk free: {metrics.disk_free_gb:.1f}GB")
                
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(self.check_interval)
    
    def _add_alert(self, alert_type: str, message: str) -> None:
        """アラートを追加."""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._alerts.append(alert)
        logger.warning(f"Resource alert: {alert_type} - {message}")
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """アラートを取得."""
        return self._alerts


class GracefulShutdown:
    """グレースフルシャットダウン.
    
    SIGINT/SIGTERMを捕捉し、クリーンに終了。
    """
    
    def __init__(self):
        self._shutdown_requested = False
        self._cleanup_handlers: List[Callable] = []
    
    def register(self) -> None:
        """シグナルハンドラを登録."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        logger.info("Graceful shutdown registered")
    
    def add_cleanup(self, handler: Callable) -> None:
        """クリーンアップハンドラを追加."""
        self._cleanup_handlers.append(handler)
    
    def _handle_signal(self, signum: int, frame: Any) -> None:
        """シグナルハンドラ."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self._shutdown_requested = True
        
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Cleanup handler error: {e}")
        
        sys.exit(0)
    
    def is_shutdown_requested(self) -> bool:
        """シャットダウンが要求されたか."""
        return self._shutdown_requested


class AutoRecovery:
    """自動復旧.
    
    エラー後の自動復旧を試みる。
    """
    
    def __init__(self, max_retries: int = 3, backoff_seconds: float = 5.0):
        self.max_retries = max_retries
        self.backoff = backoff_seconds
    
    def with_recovery(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """復旧付きで関数を実行."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise last_error


# グローバルインスタンス
_monitor: Optional[ResourceMonitor] = None
_shutdown: Optional[GracefulShutdown] = None


def init_resilience() -> None:
    """耐久機能を初期化."""
    global _monitor, _shutdown
    
    _monitor = ResourceMonitor()
    _shutdown = GracefulShutdown()
    
    _shutdown.register()
    _shutdown.add_cleanup(_monitor.stop)
    
    _monitor.start()


def get_resource_metrics() -> ResourceMetrics:
    """リソースメトリクスを取得."""
    if _monitor:
        return _monitor.get_metrics()
    return ResourceMetrics()
