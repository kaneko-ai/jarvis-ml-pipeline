"""Offline Mode Manager for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.5: オフラインモード
Manages offline detection, fallback strategies, and sync queue.
"""
from __future__ import annotations

import logging
import os
import socket
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConnectivityState(Enum):
    """Network connectivity state."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"  # Partial connectivity


@dataclass
class SyncItem:
    """Item queued for sync when online."""
    id: str
    operation: str  # e.g., "fetch_paper", "update_index"
    payload: Dict[str, Any]
    created_at: float
    retries: int = 0
    max_retries: int = 3


@dataclass
class OfflineConfig:
    """Offline mode configuration."""
    check_interval_seconds: int = 30
    check_hosts: List[str] = field(default_factory=lambda: [
        "8.8.8.8",  # Google DNS
        "1.1.1.1",  # Cloudflare DNS
    ])
    check_port: int = 53
    check_timeout: float = 3.0
    sync_batch_size: int = 10


class OfflineManager:
    """Manages offline mode for JARVIS.
    
    Features:
    - Network connectivity detection
    - Automatic fallback to cached data
    - Sync queue for deferred operations
    - Graceful degradation
    """
    
    def __init__(self, config: Optional[OfflineConfig] = None):
        self.config = config or OfflineConfig()
        self._state = ConnectivityState.ONLINE
        self._state_lock = threading.Lock()
        self._sync_queue: List[SyncItem] = []
        self._queue_lock = threading.Lock()
        self._on_state_change: List[Callable[[ConnectivityState], None]] = []
        self._force_offline = os.getenv("JARVIS_OFFLINE", "").lower() == "true"
        self._check_thread: Optional[threading.Thread] = None
        self._running = False
    
    @property
    def state(self) -> ConnectivityState:
        """Current connectivity state."""
        with self._state_lock:
            return self._state
    
    @property
    def is_online(self) -> bool:
        """Check if currently online."""
        return self.state == ConnectivityState.ONLINE
    
    @property
    def is_offline(self) -> bool:
        """Check if currently offline."""
        return self.state == ConnectivityState.OFFLINE or self._force_offline
    
    def force_offline(self, offline: bool = True) -> None:
        """Force offline mode."""
        self._force_offline = offline
        if offline:
            self._update_state(ConnectivityState.OFFLINE)
        else:
            self.check_connectivity()
    
    def check_connectivity(self) -> ConnectivityState:
        """Check network connectivity.
        
        Returns:
            Current connectivity state.
        """
        if self._force_offline:
            return ConnectivityState.OFFLINE
        
        successful_checks = 0
        for host in self.config.check_hosts:
            if self._can_reach(host):
                successful_checks += 1
        
        if successful_checks == len(self.config.check_hosts):
            new_state = ConnectivityState.ONLINE
        elif successful_checks > 0:
            new_state = ConnectivityState.DEGRADED
        else:
            new_state = ConnectivityState.OFFLINE
        
        self._update_state(new_state)
        return new_state
    
    def _can_reach(self, host: str) -> bool:
        """Check if host is reachable."""
        try:
            socket.setdefaulttimeout(self.config.check_timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                (host, self.config.check_port)
            )
            return True
        except (socket.error, socket.timeout):
            return False
    
    def _update_state(self, new_state: ConnectivityState) -> None:
        """Update connectivity state and notify listeners."""
        with self._state_lock:
            if self._state != new_state:
                old_state = self._state
                self._state = new_state
                logger.info(f"Connectivity changed: {old_state.value} -> {new_state.value}")
                
                # Notify listeners
                for callback in self._on_state_change:
                    try:
                        callback(new_state)
                    except Exception as e:
                        logger.error(f"State change callback error: {e}")
                
                # Process sync queue when coming online
                if new_state == ConnectivityState.ONLINE:
                    self._process_sync_queue()
    
    def on_state_change(self, callback: Callable[[ConnectivityState], None]) -> None:
        """Register callback for state changes."""
        self._on_state_change.append(callback)
    
    def queue_for_sync(
        self,
        operation: str,
        payload: Dict[str, Any],
        item_id: Optional[str] = None,
    ) -> str:
        """Queue an operation for when online.
        
        Args:
            operation: Operation name.
            payload: Operation data.
            item_id: Optional custom ID.
            
        Returns:
            Sync item ID.
        """
        import uuid
        
        item = SyncItem(
            id=item_id or str(uuid.uuid4()),
            operation=operation,
            payload=payload,
            created_at=time.time(),
        )
        
        with self._queue_lock:
            self._sync_queue.append(item)
        
        logger.debug(f"Queued for sync: {operation} (id={item.id})")
        return item.id
    
    def get_sync_queue(self) -> List[SyncItem]:
        """Get current sync queue."""
        with self._queue_lock:
            return list(self._sync_queue)
    
    def clear_sync_queue(self) -> int:
        """Clear sync queue.
        
        Returns:
            Number of items cleared.
        """
        with self._queue_lock:
            count = len(self._sync_queue)
            self._sync_queue.clear()
            return count
    
    def _process_sync_queue(self) -> None:
        """Process sync queue (called when coming online)."""
        with self._queue_lock:
            pending = len(self._sync_queue)
            if pending > 0:
                logger.info(f"Processing sync queue: {pending} items")
            # Actual processing would be done by registered handlers
    
    def start_monitoring(self) -> None:
        """Start background connectivity monitoring."""
        if self._running:
            return
        
        self._running = True
        self._check_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
        )
        self._check_thread.start()
        logger.info("Started connectivity monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)
            self._check_thread = None
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                self.check_connectivity()
            except Exception as e:
                logger.error(f"Connectivity check error: {e}")
            
            time.sleep(self.config.check_interval_seconds)
    
    def with_fallback(
        self,
        online_func: Callable[[], Any],
        offline_func: Callable[[], Any],
    ) -> Any:
        """Execute with automatic fallback.
        
        Args:
            online_func: Function to call when online.
            offline_func: Fallback function when offline.
            
        Returns:
            Result from either function.
        """
        if self.is_offline:
            return offline_func()
        
        try:
            return online_func()
        except (socket.error, ConnectionError) as e:
            logger.warning(f"Online operation failed, falling back: {e}")
            self._update_state(ConnectivityState.OFFLINE)
            return offline_func()
    
    def status(self) -> Dict[str, Any]:
        """Get current offline manager status."""
        return {
            "state": self.state.value,
            "is_online": self.is_online,
            "is_offline": self.is_offline,
            "force_offline": self._force_offline,
            "monitoring": self._running,
            "sync_queue_size": len(self._sync_queue),
        }


# Singleton instance
_default_manager: Optional[OfflineManager] = None


def get_offline_manager() -> OfflineManager:
    """Get default offline manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = OfflineManager()
    return _default_manager
