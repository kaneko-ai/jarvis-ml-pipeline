"""Sentry Error Tracking for JARVIS.

Per RP-535, implements error tracking and reporting.
"""
from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from functools import wraps
import hashlib


class ErrorLevel(Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class ErrorEvent:
    """An error event."""
    event_id: str
    level: ErrorLevel
    message: str
    exception_type: Optional[str] = None
    exception_value: Optional[str] = None
    stacktrace: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    user_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    fingerprint: Optional[str] = None


@dataclass
class SentryConfig:
    """Sentry configuration."""
    dsn: str = ""
    environment: str = "development"
    release: str = ""
    sample_rate: float = 1.0
    max_breadcrumbs: int = 100
    attach_stacktrace: bool = True
    send_default_pii: bool = False


class SentryClient:
    """Sentry-compatible error tracking client.
    
    Per RP-535:
    - Capture exceptions
    - Capture messages
    - Breadcrumbs
    - User context
    - Tags and extra data
    """
    
    def __init__(self, config: Optional[SentryConfig] = None):
        self.config = config or SentryConfig(
            dsn=os.getenv("SENTRY_DSN", ""),
            environment=os.getenv("JARVIS_ENV", "development"),
        )
        self._enabled = bool(self.config.dsn)
        self._breadcrumbs: List[Dict[str, Any]] = []
        self._user: Optional[Dict[str, Any]] = None
        self._tags: Dict[str, str] = {}
        self._events: List[ErrorEvent] = []
    
    def is_enabled(self) -> bool:
        """Check if Sentry is enabled."""
        return self._enabled
    
    def capture_exception(
        self,
        exception: Optional[Exception] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture an exception.
        
        Args:
            exception: Exception to capture.
            **kwargs: Additional data.
            
        Returns:
            Event ID if captured.
        """
        if not self._should_sample():
            return None
        
        exc = exception
        if exc is None:
            # Get current exception
            import sys
            exc_info = sys.exc_info()
            if exc_info[1]:
                exc = exc_info[1]
        
        if exc is None:
            return None
        
        event = ErrorEvent(
            event_id=self._generate_event_id(),
            level=ErrorLevel.ERROR,
            message=str(exc),
            exception_type=type(exc).__name__,
            exception_value=str(exc),
            stacktrace=traceback.format_exc() if self.config.attach_stacktrace else None,
            user_id=self._user.get("id") if self._user else None,
            tags={**self._tags, **kwargs.get("tags", {})},
            extra=kwargs.get("extra", {}),
            fingerprint=self._compute_fingerprint(exc),
        )
        
        self._events.append(event)
        self._send_event(event)
        
        return event.event_id
    
    def capture_message(
        self,
        message: str,
        level: ErrorLevel = ErrorLevel.INFO,
        **kwargs,
    ) -> Optional[str]:
        """Capture a message.
        
        Args:
            message: Message to capture.
            level: Message level.
            **kwargs: Additional data.
            
        Returns:
            Event ID if captured.
        """
        if not self._should_sample():
            return None
        
        event = ErrorEvent(
            event_id=self._generate_event_id(),
            level=level,
            message=message,
            user_id=self._user.get("id") if self._user else None,
            tags={**self._tags, **kwargs.get("tags", {})},
            extra=kwargs.get("extra", {}),
        )
        
        self._events.append(event)
        self._send_event(event)
        
        return event.event_id
    
    def add_breadcrumb(
        self,
        category: str,
        message: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a breadcrumb.
        
        Args:
            category: Breadcrumb category.
            message: Breadcrumb message.
            level: Breadcrumb level.
            data: Additional data.
        """
        breadcrumb = {
            "category": category,
            "message": message,
            "level": level,
            "timestamp": time.time(),
            "data": data or {},
        }
        
        self._breadcrumbs.append(breadcrumb)
        
        # Trim old breadcrumbs
        if len(self._breadcrumbs) > self.config.max_breadcrumbs:
            self._breadcrumbs = self._breadcrumbs[-self.config.max_breadcrumbs:]
    
    def set_user(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Set user context.
        
        Args:
            user_id: User ID.
            email: User email.
            username: Username.
            **kwargs: Additional user data.
        """
        self._user = {
            "id": user_id,
            "email": email if self.config.send_default_pii else None,
            "username": username,
            **kwargs,
        }
    
    def set_tag(self, key: str, value: str) -> None:
        """Set a tag.
        
        Args:
            key: Tag key.
            value: Tag value.
        """
        self._tags[key] = value
    
    def set_extra(self, key: str, value: Any) -> None:
        """Set extra data.
        
        Args:
            key: Extra key.
            value: Extra value.
        """
        # Store in tags for simplicity
        self._tags[f"extra.{key}"] = str(value)
    
    def get_last_event_id(self) -> Optional[str]:
        """Get last captured event ID."""
        return self._events[-1].event_id if self._events else None
    
    def get_events(self) -> List[ErrorEvent]:
        """Get all captured events (for testing)."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear captured events (for testing)."""
        self._events.clear()
    
    def _should_sample(self) -> bool:
        """Check if event should be sampled."""
        import random
        return random.random() < self.config.sample_rate
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        return uuid.uuid4().hex
    
    def _compute_fingerprint(self, exc: Exception) -> str:
        """Compute exception fingerprint for grouping."""
        content = f"{type(exc).__name__}:{str(exc)}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _send_event(self, event: ErrorEvent) -> None:
        """Send event to Sentry (mock in development)."""
        # In production, send to Sentry API
        pass


# Global client
_sentry_client: Optional[SentryClient] = None


def init_sentry(dsn: Optional[str] = None, **kwargs) -> SentryClient:
    """Initialize Sentry client."""
    global _sentry_client
    config = SentryConfig(dsn=dsn or "", **kwargs)
    _sentry_client = SentryClient(config)
    return _sentry_client


def get_sentry() -> SentryClient:
    """Get global Sentry client."""
    global _sentry_client
    if _sentry_client is None:
        _sentry_client = SentryClient()
    return _sentry_client


def capture_exception(exception: Optional[Exception] = None, **kwargs) -> Optional[str]:
    """Capture exception helper."""
    return get_sentry().capture_exception(exception, **kwargs)


def capture_message(message: str, level: ErrorLevel = ErrorLevel.INFO, **kwargs) -> Optional[str]:
    """Capture message helper."""
    return get_sentry().capture_message(message, level, **kwargs)


def sentry_trace(func: Callable) -> Callable:
    """Decorator to capture exceptions from a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            capture_exception(e, extra={"function": func.__name__})
            raise
    return wrapper
