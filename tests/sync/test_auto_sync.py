from unittest.mock import MagicMock, patch

from jarvis_core.network.degradation import DegradationLevel
from jarvis_core.sync.auto_sync import on_network_restored


def test_on_network_restored_offline():
    with patch('jarvis_core.sync.auto_sync.get_degradation_manager') as mock_get_manager:
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        on_network_restored(is_online=False)

        mock_manager.set_level.assert_called_with(DegradationLevel.OFFLINE)

def test_on_network_restored_online_no_pending():
    with patch('jarvis_core.sync.auto_sync.get_degradation_manager') as mock_get_manager, \
         patch('jarvis_core.sync.auto_sync.SyncQueueManager') as mock_queue_manager_cls:

        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        mock_queue = MagicMock()
        mock_queue_manager_cls.return_value = mock_queue
        mock_queue.get_queue_status.return_value = {"pending": 0}

        on_network_restored(is_online=True)

        mock_manager.set_level.assert_called_with(DegradationLevel.FULL)
        mock_queue.process_queue.assert_not_called()

def test_on_network_restored_online_with_pending():
    with patch('jarvis_core.sync.auto_sync.get_degradation_manager') as mock_get_manager, \
         patch('jarvis_core.sync.auto_sync.SyncQueueManager') as mock_queue_manager_cls, \
         patch('threading.Thread') as mock_thread_cls:

        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        mock_queue = MagicMock()
        mock_queue_manager_cls.return_value = mock_queue
        mock_queue.get_queue_status.return_value = {"pending": 5}

        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        on_network_restored(is_online=True)

        mock_manager.set_level.assert_called_with(DegradationLevel.FULL)
        mock_thread_cls.assert_called()
        mock_thread.start.assert_called()
