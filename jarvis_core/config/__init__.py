"""Config package for JARVIS."""

from .feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    RolloutStrategy,
    feature_flag,
    get_feature_flags,
)

# TODO(deprecate): Backwards compatibility re-exports from config_utils
try:
    from jarvis_core.config_utils import Config, JarvisConfig, get_default_config, load_config
except ImportError:
    get_default_config = None
    load_config = None
    JarvisConfig = None
    Config = None

__all__ = [
    "FeatureFlagManager",
    "FeatureFlag",
    "RolloutStrategy",
    "get_feature_flags",
    "feature_flag",
    "get_default_config",
    "load_config",
    "JarvisConfig",
    "Config",
]