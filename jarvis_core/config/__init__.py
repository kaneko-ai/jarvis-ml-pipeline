"""Config package for JARVIS."""
from .feature_flags import (
    FeatureFlagManager,
    FeatureFlag,
    RolloutStrategy,
    get_feature_flags,
    feature_flag,
)

# TODO(deprecate): Backwards compatibility re-exports from config_utils
try:
    from jarvis_core.config_utils import get_default_config, load_config, JarvisConfig, Config
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

