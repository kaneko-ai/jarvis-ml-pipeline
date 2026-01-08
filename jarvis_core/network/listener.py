import logging
import threading
import time
from collections.abc import Callable

from jarvis_core.network.detector import is_online

logger = logging.getLogger(__name__)


class NetworkChangeListener:
    def __init__(self, check_interval: float = 5.0):
        self._check_interval = check_interval
        self._callbacks: list[Callable[[bool], None]] = []
        self._last_status: bool = True  # Assuming start online, or check initial?
        self._running = False
        self._thread: threading.Thread | None = None

    def add_callback(self, callback: Callable[[bool], None]) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return

        # Initial check
        self._last_status = is_online()

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.debug("Network listener started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.debug("Network listener stopped")

    def _monitor_loop(self) -> None:
        while self._running:
            current_status = is_online(
                force_check=True
            )  # Should probably not force check every time to save bandwidth, but for detection we need it?
            # Actually is_online has internal cache if force_check=False.
            # If we want to detect changes, we rely on cache expiration or force check.
            # Assuming cache ttl is handled by detector.

            if current_status != self._last_status:
                logger.info(f"Network status changed: {self._last_status} -> {current_status}")
                for callback in self._callbacks:
                    try:
                        callback(current_status)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                self._last_status = current_status

            time.sleep(self._check_interval)
