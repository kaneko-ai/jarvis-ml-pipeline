"""Recording utilities for browser actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass
class BrowserRecorder:
    """Capture browser screenshots as a recording."""

    session_id: str
    base_dir: Path = Path("logs/browser_recordings")
    frame_paths: list[Path] = field(default_factory=list)
    active: bool = False

    def start_recording(self) -> None:
        self.active = True
        self.frame_paths.clear()
        self._ensure_dir()

    def capture_frame(self, image_bytes: bytes | None = None) -> Path:
        if not self.active:
            raise RuntimeError("Recording is not active.")
        if image_bytes is None:
            raise ValueError("image_bytes is required to capture a frame.")
        frame_index = len(self.frame_paths) + 1
        frame_path = self._session_dir() / f"frame_{frame_index:04d}.png"
        frame_path.write_bytes(image_bytes)
        self.frame_paths.append(frame_path)
        return frame_path

    def stop_recording(self) -> Path:
        if not self.active:
            self._ensure_dir()
            return self._session_dir()
        self.active = False
        return self._session_dir()

    def list_frames(self) -> Iterable[Path]:
        return list(self.frame_paths)

    def _ensure_dir(self) -> None:
        self._session_dir().mkdir(parents=True, exist_ok=True)

    def _session_dir(self) -> Path:
        return self.base_dir / self.session_id


def generate_session_id(prefix: str = "browser") -> str:
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{timestamp}"
