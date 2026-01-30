from jarvis_core.network.degradation import DegradationLevel, get_degradation_manager


def get_status_banner() -> str:
    manager = get_degradation_manager()
    level = manager.get_level()

    banners = {
        DegradationLevel.FULL: "",
        DegradationLevel.LIMITED: "⚠️  Limited Mode: External APIs unavailable",
        DegradationLevel.OFFLINE: "🔌 Offline Mode: Using local cache only",
        DegradationLevel.CRITICAL: "🚨 Critical: No cache available",
    }

    return banners.get(level, "")