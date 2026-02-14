"""Telemetry models for ops_extract runtime monitoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetryPoint:
    ts_iso: str
    net_sent_bytes_total: int
    net_recv_bytes_total: int
    net_sent_bps: float
    net_recv_bps: float
    rss_mb: float
    vms_mb: float
    cpu_percent: float
    crash_risk_percent: float


@dataclass(frozen=True)
class ProgressPoint:
    ts_iso: str
    stage: str
    stage_progress_percent: float
    overall_progress_percent: float
    items_done: int
    items_total: int
    eta_seconds: float | None
    eta_confidence_percent: float
