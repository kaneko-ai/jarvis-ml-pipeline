"""Contracts and defaults for ops_extract mode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

OPS_EXTRACT_VERSION = "ops_extract_v1"
OPS_EXTRACT_SCHEMA_VERSION = "ops_extract_contract_v2"
OPS_EXTRACT_SYNC_STATE_VERSION = "ops_extract_sync_v2"
OPS_EXTRACT_CONFIG_SCHEMA_VERSION = "2.0"

OPS_EXTRACT_DEPRECATED_KEYS = {
    "sync_chunk_size": "sync.chunk_bytes",
    "drive_api_url": "drive.api_base_url",
    "drive_upload_url": "drive.upload_base_url",
    "trace": "trace_enabled",
    "resume": "resume_enabled",
}

OPS_EXTRACT_OPTIONAL_ARTIFACTS = [
    "manifest.json",
    "run_metadata.json",
    "metrics.json",
    "warnings.json",
    "failure_analysis.json",
    "sync_state.json",
    "stage_cache.json",
    "trace.jsonl",
    "ingestion/pdf_diagnosis.json",
    "ingestion/text.md",
    "ingestion/text_source.json",
    "ocr/ocr_meta.json",
]


@dataclass(frozen=True)
class OpsExtractThresholds:
    min_total_chars: int = 800
    min_chars_per_page: int = 200
    empty_page_ratio_threshold: float = 0.6


@dataclass(frozen=True)
class OpsExtractConfig:
    config_schema_version: str = OPS_EXTRACT_CONFIG_SCHEMA_VERSION
    enabled: bool = False
    parse_workers: int = 2
    ocr_workers: int = 2
    upload_workers: int = 4
    thresholds: OpsExtractThresholds = OpsExtractThresholds()
    yomitoku_mode: str = "normal"
    yomitoku_figure: bool = True
    sync_enabled: bool = False
    sync_dry_run: bool = True
    sync_max_retries: int = 3
    sync_retry_backoff_sec: float = 2.0
    sync_verify_sha256: bool = True
    sync_chunk_bytes: int = 8 * 1024 * 1024
    drive_access_token: str | None = None
    drive_folder_id: str | None = None
    drive_api_base_url: str | None = None
    drive_upload_base_url: str | None = None
    preflight_rule_mode: str = "strict"
    lessons_path: str | None = None
    stop_on_preflight_failure: bool = True
    min_disk_free_gb: float = 1.0
    trace_enabled: bool = True
    resume_enabled: bool = True
    retention_failed_days: int = 30
    retention_success_days: int = 180
    retention_trash_days: int = 7
    retention_max_delete_per_run: int = 200
    retention_dry_run: bool = False
    dry_run: bool = False


def build_ops_extract_config(raw: dict[str, Any] | None) -> OpsExtractConfig:
    """Build config from run_config.extra.ops_extract style dict."""
    raw = raw or {}
    thresholds_raw = raw.get("thresholds") or {}
    yomitoku_raw = raw.get("yomitoku") or {}
    sync_raw = raw.get("sync") or {}
    preflight_raw = raw.get("preflight") or {}
    retention_raw = raw.get("retention") or {}
    drive_raw = raw.get("drive") or {}

    preflight_rule_mode = (
        str(preflight_raw.get("rule_mode", raw.get("preflight_rule_mode", "strict")))
        .strip()
        .lower()
    )
    if preflight_rule_mode not in {"strict", "warn"}:
        preflight_rule_mode = "strict"

    sync_chunk_legacy = raw.get("sync_chunk_size")
    if sync_chunk_legacy is None:
        sync_chunk_legacy = raw.get("sync_chunk_bytes")

    drive_api_legacy = raw.get("drive_api_url")
    if drive_api_legacy is None:
        drive_api_legacy = raw.get("drive_api_base_url")

    drive_upload_legacy = raw.get("drive_upload_url")
    if drive_upload_legacy is None:
        drive_upload_legacy = raw.get("drive_upload_base_url")

    trace_legacy = raw.get("trace")
    resume_legacy = raw.get("resume")

    thresholds = OpsExtractThresholds(
        min_total_chars=int(thresholds_raw.get("min_total_chars", 800)),
        min_chars_per_page=int(thresholds_raw.get("min_chars_per_page", 200)),
        empty_page_ratio_threshold=float(thresholds_raw.get("empty_page_ratio_threshold", 0.6)),
    )

    return OpsExtractConfig(
        config_schema_version=str(
            raw.get("config_schema_version", OPS_EXTRACT_CONFIG_SCHEMA_VERSION)
        ),
        enabled=bool(raw.get("enabled", False)),
        parse_workers=int(raw.get("parse_workers", 2)),
        ocr_workers=int(raw.get("ocr_workers", 2)),
        upload_workers=int(raw.get("upload_workers", 4)),
        thresholds=thresholds,
        yomitoku_mode=str(yomitoku_raw.get("mode", "normal")),
        yomitoku_figure=bool(yomitoku_raw.get("figure", True)),
        sync_enabled=bool(sync_raw.get("enabled", False)),
        sync_dry_run=bool(sync_raw.get("dry_run", True)),
        sync_max_retries=int(sync_raw.get("max_retries", 3)),
        sync_retry_backoff_sec=float(sync_raw.get("retry_backoff_sec", 2.0)),
        sync_verify_sha256=bool(sync_raw.get("verify_sha256", True)),
        sync_chunk_bytes=int(sync_raw.get("chunk_bytes", sync_chunk_legacy or 8 * 1024 * 1024)),
        drive_access_token=drive_raw.get("access_token"),
        drive_folder_id=drive_raw.get("folder_id"),
        drive_api_base_url=drive_raw.get("api_base_url") or drive_api_legacy,
        drive_upload_base_url=drive_raw.get("upload_base_url") or drive_upload_legacy,
        preflight_rule_mode=preflight_rule_mode,
        lessons_path=raw.get("lessons_path"),
        stop_on_preflight_failure=bool(raw.get("stop_on_preflight_failure", True)),
        min_disk_free_gb=float(raw.get("min_disk_free_gb", 1.0)),
        trace_enabled=bool(
            raw.get("trace_enabled", trace_legacy if trace_legacy is not None else True)
        ),
        resume_enabled=bool(
            raw.get("resume_enabled", resume_legacy if resume_legacy is not None else True)
        ),
        retention_failed_days=int(retention_raw.get("failed_days", 30)),
        retention_success_days=int(retention_raw.get("success_days", 180)),
        retention_trash_days=int(retention_raw.get("trash_days", 7)),
        retention_max_delete_per_run=int(retention_raw.get("max_delete_per_run", 200)),
        retention_dry_run=bool(retention_raw.get("dry_run", False)),
        dry_run=bool(raw.get("dry_run", False)),
    )


def expected_optional_paths(run_dir: Path, include_ocr_meta: bool) -> list[Path]:
    """Return optional artifact paths for existence checks."""
    candidates = [
        run_dir / "manifest.json",
        run_dir / "run_metadata.json",
        run_dir / "metrics.json",
        run_dir / "warnings.json",
        run_dir / "failure_analysis.json",
        run_dir / "sync_state.json",
        run_dir / "stage_cache.json",
        run_dir / "trace.jsonl",
        run_dir / "ingestion" / "pdf_diagnosis.json",
        run_dir / "ingestion" / "text.md",
        run_dir / "ingestion" / "text_source.json",
    ]
    if include_ocr_meta:
        candidates.append(run_dir / "ocr" / "ocr_meta.json")
    return candidates
