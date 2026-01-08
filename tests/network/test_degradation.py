import pytest
from jarvis_core.network.degradation import (
    DegradationLevel,
    DegradationManager,
    get_degradation_manager
)

@pytest.fixture
def manager():
    mgr = DegradationManager.get_instance()
    # Reset state
    mgr._current_level = DegradationLevel.FULL
    mgr._listeners = []
    # If using singleton, be careful about state between tests
    return mgr

def test_degradation_level_enum():
    assert DegradationLevel.FULL.value == "full"
    assert DegradationLevel.OFFLINE.value == "offline"

def test_manager_level_change(manager):
    events = []
    def listener(old, new):
        events.append((old, new))
    
    manager.add_listener(listener)
    manager.set_level(DegradationLevel.OFFLINE)
    
    assert manager.get_level() == DegradationLevel.OFFLINE
    assert len(events) == 1
    assert events[0] == (DegradationLevel.FULL, DegradationLevel.OFFLINE)

def test_auto_detect_online():
    # Mocking would be needed for real network check
    # For now, just ensuring it runs without error and returns a valid level
    manager = DegradationManager()
    level = manager.auto_detect_level()
    assert isinstance(level, DegradationLevel)

def test_singleton():
    m1 = get_degradation_manager()
    m2 = get_degradation_manager()
    assert m1 is m2
