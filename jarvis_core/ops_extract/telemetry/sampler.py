"""Telemetry sampler for ops_extract runtime."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .models import TelemetryPoint

LOGGER = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TelemetrySampler:
    """Background sampler that appends telemetry points to telemetry.jsonl."""

    def __init__(
        self,
        run_dir: Path,
        *,
        interval_sec: float = 0.5,
        recent_exceptions_count_fn: Callable[[], int] | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.interval_sec = max(0.1, float(interval_sec))
        self.path = self.run_dir / "telemetry.jsonl"
        self._recent_exceptions_count_fn = recent_exceptions_count_fn or (lambda: 0)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        try:
            import psutil  # type: ignore
        except Exception:
            self._enabled = False
            return
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            kwargs={"psutil_mod": psutil},
            daemon=True,
            name="ops_extract_telemetry",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def __del__(self) -> None:  # pragma: no cover
        try:
            self.stop()
        except Exception as exc:
            LOGGER.debug("telemetry sampler stop on GC failed: %s", exc)

    def _run_loop(self, *, psutil_mod) -> None:
        process = psutil_mod.Process(os.getpid())
        prev = psutil_mod.net_io_counters()
        prev_ts = time.perf_counter()
        # Prime CPU percent baseline.
        process.cpu_percent(interval=None)
        while not self._stop.is_set():
            time.sleep(self.interval_sec)
            now = psutil_mod.net_io_counters()
            now_ts = time.perf_counter()
            dt = max(1e-6, now_ts - prev_ts)
            sent_bps = float(now.bytes_sent - prev.bytes_sent) / dt
            recv_bps = float(now.bytes_recv - prev.bytes_recv) / dt
            prev = now
            prev_ts = now_ts

            mem = process.memory_info()
            vm = psutil_mod.virtual_memory()
            rss_mb = float(mem.rss) / (1024.0 * 1024.0)
            vms_mb = float(mem.vms) / (1024.0 * 1024.0)
            cpu_percent = float(process.cpu_percent(interval=None))
            available_mb = max(1.0, float(vm.available) / (1024.0 * 1024.0))
            mem_ratio = rss_mb / available_mb
            risk = self._crash_risk_percent(mem_ratio=mem_ratio)
            try:
                recent_ex = int(self._recent_exceptions_count_fn())
            except Exception:
                recent_ex = 0
            if recent_ex > 0:
                risk = min(100.0, risk + 10.0)

            point = TelemetryPoint(
                ts_iso=_now_iso(),
                net_sent_bytes_total=int(now.bytes_sent),
                net_recv_bytes_total=int(now.bytes_recv),
                net_sent_bps=round(sent_bps, 4),
                net_recv_bps=round(recv_bps, 4),
                rss_mb=round(rss_mb, 4),
                vms_mb=round(vms_mb, 4),
                cpu_percent=round(cpu_percent, 4),
                crash_risk_percent=round(risk, 2),
            )
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(point.__dict__, ensure_ascii=False) + "\n")

    @staticmethod
    def _crash_risk_percent(*, mem_ratio: float) -> float:
        if mem_ratio < 0.5:
            return 5.0
        if mem_ratio < 0.7:
            return 20.0
        if mem_ratio < 0.85:
            return 50.0
        if mem_ratio < 0.93:
            return 75.0
        return 90.0
