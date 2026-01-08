from typing import Callable, List

class SyncProgressReporter:
    def __init__(self):
        self._callbacks: List[Callable[[int, int], None]] = []
    
    def add_callback(self, callback: Callable[[int, int], None]) -> None:
        self._callbacks.append(callback)
    
    def report(self, completed: int, total: int) -> None:
        for callback in self._callbacks:
            callback(completed, total)
