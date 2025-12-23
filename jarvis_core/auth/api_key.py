"""API Key Authentication for JARVIS.

Implements API key validation and management.
"""
from __future__ import annotations

import os
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from functools import wraps


@dataclass
class APIKey:
    """An API key."""
    key_id: str
    key_hash: str
    name: str
    created_at: float
    expires_at: Optional[float] = None
    scopes: Set[str] = field(default_factory=set)
    rate_limit: int = 1000  # requests per hour
    enabled: bool = True


@dataclass
class AuthResult:
    """Authentication result."""
    success: bool
    key_id: Optional[str] = None
    error: Optional[str] = None
    scopes: Set[str] = field(default_factory=set)


class APIKeyManager:
    """Manages API key authentication.
    
    Features:
    - Key generation
    - Key validation
    - Scope-based access control
    - Rate limiting
    """
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or os.getenv("API_SECRET", "jarvis-default-secret")
        self._keys: Dict[str, APIKey] = {}
        self._usage: Dict[str, List[float]] = {}  # key_id -> timestamps
    
    def generate_key(
        self,
        name: str,
        scopes: Optional[Set[str]] = None,
        expires_days: Optional[int] = None,
        rate_limit: int = 1000,
    ) -> str:
        """Generate a new API key.
        
        Args:
            name: Key name/description.
            scopes: Allowed scopes.
            expires_days: Days until expiration.
            rate_limit: Requests per hour.
            
        Returns:
            The generated API key.
        """
        import secrets
        
        # Generate key
        raw_key = secrets.token_urlsafe(32)
        key_id = secrets.token_hex(8)
        key_hash = self._hash_key(raw_key)
        
        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = time.time() + (expires_days * 86400)
        
        # Store key metadata
        self._keys[key_id] = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            created_at=time.time(),
            expires_at=expires_at,
            scopes=scopes or {"read"},
            rate_limit=rate_limit,
            enabled=True,
        )
        
        # Return full key (only time it's visible)
        return f"{key_id}.{raw_key}"
    
    def validate(
        self,
        api_key: str,
        required_scope: Optional[str] = None,
    ) -> AuthResult:
        """Validate an API key.
        
        Args:
            api_key: The API key to validate.
            required_scope: Required scope (optional).
            
        Returns:
            Authentication result.
        """
        if not api_key:
            return AuthResult(success=False, error="No API key provided")
        
        # Parse key
        parts = api_key.split(".", 1)
        if len(parts) != 2:
            return AuthResult(success=False, error="Invalid key format")
        
        key_id, raw_key = parts
        
        # Find key
        key_meta = self._keys.get(key_id)
        if not key_meta:
            return AuthResult(success=False, error="Key not found")
        
        # Check if enabled
        if not key_meta.enabled:
            return AuthResult(success=False, error="Key is disabled")
        
        # Check expiration
        if key_meta.expires_at and time.time() > key_meta.expires_at:
            return AuthResult(success=False, error="Key has expired")
        
        # Verify hash
        if not self._verify_key(raw_key, key_meta.key_hash):
            return AuthResult(success=False, error="Invalid key")
        
        # Check scope
        if required_scope and required_scope not in key_meta.scopes:
            return AuthResult(
                success=False,
                error=f"Missing required scope: {required_scope}",
                key_id=key_id,
            )
        
        # Check rate limit
        if not self._check_rate_limit(key_id, key_meta.rate_limit):
            return AuthResult(
                success=False,
                error="Rate limit exceeded",
                key_id=key_id,
            )
        
        # Record usage
        self._record_usage(key_id)
        
        return AuthResult(
            success=True,
            key_id=key_id,
            scopes=key_meta.scopes,
        )
    
    def revoke(self, key_id: str) -> bool:
        """Revoke an API key.
        
        Args:
            key_id: Key ID to revoke.
            
        Returns:
            True if revoked.
        """
        if key_id in self._keys:
            self._keys[key_id].enabled = False
            return True
        return False
    
    def list_keys(self) -> List[Dict]:
        """List all API keys (metadata only)."""
        return [
            {
                "key_id": k.key_id,
                "name": k.name,
                "created_at": k.created_at,
                "expires_at": k.expires_at,
                "scopes": list(k.scopes),
                "enabled": k.enabled,
            }
            for k in self._keys.values()
        ]
    
    def _hash_key(self, raw_key: str) -> str:
        """Hash an API key."""
        return hashlib.sha256(
            f"{self.secret}:{raw_key}".encode()
        ).hexdigest()
    
    def _verify_key(self, raw_key: str, stored_hash: str) -> bool:
        """Verify a key against stored hash."""
        computed = self._hash_key(raw_key)
        return hmac.compare_digest(computed, stored_hash)
    
    def _check_rate_limit(self, key_id: str, limit: int) -> bool:
        """Check if key is within rate limit."""
        now = time.time()
        hour_ago = now - 3600
        
        usage = self._usage.get(key_id, [])
        recent = [t for t in usage if t > hour_ago]
        
        return len(recent) < limit
    
    def _record_usage(self, key_id: str) -> None:
        """Record API key usage."""
        if key_id not in self._usage:
            self._usage[key_id] = []
        
        self._usage[key_id].append(time.time())
        
        # Cleanup old entries
        hour_ago = time.time() - 3600
        self._usage[key_id] = [
            t for t in self._usage[key_id] if t > hour_ago
        ]


# Global manager
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def require_api_key(scope: Optional[str] = None):
    """Decorator to require API key authentication."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, api_key: str = "", **kwargs):
            manager = get_api_key_manager()
            result = manager.validate(api_key, scope)
            
            if not result.success:
                raise PermissionError(result.error)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
