from __future__ import annotations

import builtins
from pathlib import Path

from jarvis_core.ops_extract.telemetry.sampler import TelemetrySampler


def test_telemetry_sampler_graceful_without_psutil(monkeypatch, tmp_path: Path) -> None:
    original_import = builtins.__import__

    def _patched_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("psutil missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _patched_import)
    sampler = TelemetrySampler(tmp_path / "run")
    sampler.start()
    assert sampler.enabled is False
    sampler.stop()
