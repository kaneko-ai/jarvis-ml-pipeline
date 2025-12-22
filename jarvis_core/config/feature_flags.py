"""Feature Flags.

Per RP-525, implements feature flag management.
"""
from __future__ import annotations

import hashlib
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class RolloutStrategy(Enum):
    """Feature rollout strategies."""
    
    ALL = "all"
    NONE = "none"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    GROUP = "group"


@dataclass
class FeatureFlag:
    """A feature flag."""
    
    name: str
    description: str
    enabled: bool = False
    strategy: RolloutStrategy = RolloutStrategy.NONE
    percentage: float = 0.0
    user_list: Set[str] = field(default_factory=set)
    groups: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class FeatureFlagManager:
    """Feature flag management.
    
    Per RP-525:
    - Kill switches
    - Gradual rollout
    - A/B experiments
    - User targeting
    """
    
    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._lock = threading.RLock()
        self._decision_cache: Dict[str, Dict[str, bool]] = {}
    
    def create_flag(
        self,
        name: str,
        description: str = "",
        enabled: bool = False,
        strategy: RolloutStrategy = RolloutStrategy.NONE,
        percentage: float = 0.0,
    ) -> FeatureFlag:
        """Create a feature flag.
        
        Args:
            name: Flag name.
            description: Description.
            enabled: Initial state.
            strategy: Rollout strategy.
            percentage: Rollout percentage.
            
        Returns:
            Created flag.
        """
        flag = FeatureFlag(
            name=name,
            description=description,
            enabled=enabled,
            strategy=strategy,
            percentage=percentage,
        )
        
        with self._lock:
            self._flags[name] = flag
            self._decision_cache[name] = {}
        
        return flag
    
    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag.
        
        Args:
            name: Flag name.
            
        Returns:
            FeatureFlag or None.
        """
        return self._flags.get(name)
    
    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        groups: Optional[List[str]] = None,
        default: bool = False,
    ) -> bool:
        """Check if flag is enabled for user.
        
        Args:
            flag_name: Flag name.
            user_id: Optional user ID.
            groups: Optional user groups.
            default: Default value if flag not found.
            
        Returns:
            True if enabled.
        """
        flag = self._flags.get(flag_name)
        
        if not flag:
            return default
        
        if not flag.enabled:
            return False
        
        # Check cache for user
        if user_id:
            cached = self._decision_cache.get(flag_name, {}).get(user_id)
            if cached is not None:
                return cached
        
        # Evaluate strategy
        result = self._evaluate_strategy(flag, user_id, groups or [])
        
        # Cache result
        if user_id:
            with self._lock:
                if flag_name not in self._decision_cache:
                    self._decision_cache[flag_name] = {}
                self._decision_cache[flag_name][user_id] = result
        
        return result
    
    def _evaluate_strategy(
        self,
        flag: FeatureFlag,
        user_id: Optional[str],
        groups: List[str],
    ) -> bool:
        """Evaluate rollout strategy.
        
        Args:
            flag: Feature flag.
            user_id: User ID.
            groups: User groups.
            
        Returns:
            True if enabled.
        """
        strategy = flag.strategy
        
        if strategy == RolloutStrategy.ALL:
            return True
        
        if strategy == RolloutStrategy.NONE:
            return False
        
        if strategy == RolloutStrategy.USER_LIST:
            return user_id in flag.user_list if user_id else False
        
        if strategy == RolloutStrategy.GROUP:
            return bool(set(groups) & flag.groups)
        
        if strategy == RolloutStrategy.PERCENTAGE:
            if not user_id:
                return False
            
            # Deterministic hash-based bucketing
            hash_input = f"{flag.name}:{user_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            bucket = (hash_value % 100) / 100.0
            
            return bucket < flag.percentage
        
        return False
    
    def enable_flag(self, flag_name: str) -> None:
        """Enable a flag globally.
        
        Args:
            flag_name: Flag name.
        """
        with self._lock:
            if flag_name in self._flags:
                self._flags[flag_name].enabled = True
                self._flags[flag_name].strategy = RolloutStrategy.ALL
                self._flags[flag_name].updated_at = time.time()
                self._decision_cache[flag_name] = {}
    
    def disable_flag(self, flag_name: str) -> None:
        """Disable a flag (kill switch).
        
        Args:
            flag_name: Flag name.
        """
        with self._lock:
            if flag_name in self._flags:
                self._flags[flag_name].enabled = False
                self._flags[flag_name].updated_at = time.time()
                self._decision_cache[flag_name] = {}
    
    def set_percentage(
        self,
        flag_name: str,
        percentage: float,
    ) -> None:
        """Set rollout percentage.
        
        Args:
            flag_name: Flag name.
            percentage: Rollout percentage (0.0-1.0).
        """
        with self._lock:
            if flag_name in self._flags:
                self._flags[flag_name].percentage = min(max(percentage, 0.0), 1.0)
                self._flags[flag_name].strategy = RolloutStrategy.PERCENTAGE
                self._flags[flag_name].enabled = True
                self._flags[flag_name].updated_at = time.time()
                self._decision_cache[flag_name] = {}
    
    def add_users(
        self,
        flag_name: str,
        user_ids: List[str],
    ) -> None:
        """Add users to flag.
        
        Args:
            flag_name: Flag name.
            user_ids: User IDs to add.
        """
        with self._lock:
            if flag_name in self._flags:
                self._flags[flag_name].user_list.update(user_ids)
                self._flags[flag_name].strategy = RolloutStrategy.USER_LIST
                self._flags[flag_name].enabled = True
                self._flags[flag_name].updated_at = time.time()
    
    def list_flags(self) -> List[FeatureFlag]:
        """List all flags.
        
        Returns:
            List of flags.
        """
        return list(self._flags.values())


# Global instance
_feature_flags: Optional[FeatureFlagManager] = None


def get_feature_flags() -> FeatureFlagManager:
    """Get global feature flag manager."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlagManager()
    return _feature_flags


def feature_flag(
    flag_name: str,
    default: bool = False,
):
    """Decorator for feature-flagged functions.
    
    Args:
        flag_name: Flag name.
        default: Default value.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if get_feature_flags().is_enabled(flag_name, default=default):
                return func(*args, **kwargs)
            return None
        return wrapper
    return decorator
