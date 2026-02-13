"""Ops+Extract mode components.

This package provides an LLM-independent extraction flow focused on
operational robustness and PDF text recovery quality.
"""

from .contracts import (
    OPS_EXTRACT_OPTIONAL_ARTIFACTS,
    OPS_EXTRACT_VERSION,
    OpsExtractConfig,
    OpsExtractThresholds,
    build_ops_extract_config,
)
from .failure_analysis import build_failure_analysis, classify_failure_category
from .drive_sync import sync_run_to_drive
from .learning import (
    LESSONS_ENV_KEY,
    LESSONS_PATH,
    load_block_rules,
    record_lesson,
    resolve_lessons_path,
)
from .manifest import create_manifest_payload, write_manifest
from .metrics import build_metrics, build_text_quality_warnings
from .needs_ocr import NeedsOcrDecision, decide_needs_ocr
from .orchestrator import OpsExtractOrchestrator, OpsExtractOutcome
from .preflight import PreflightReport, run_preflight_checks
from .retention import OpsExtractRetentionResult, apply_ops_extract_retention

__all__ = [
    "OPS_EXTRACT_OPTIONAL_ARTIFACTS",
    "OPS_EXTRACT_VERSION",
    "OpsExtractThresholds",
    "OpsExtractConfig",
    "build_ops_extract_config",
    "classify_failure_category",
    "build_failure_analysis",
    "sync_run_to_drive",
    "LESSONS_ENV_KEY",
    "LESSONS_PATH",
    "load_block_rules",
    "record_lesson",
    "resolve_lessons_path",
    "create_manifest_payload",
    "write_manifest",
    "build_metrics",
    "build_text_quality_warnings",
    "NeedsOcrDecision",
    "decide_needs_ocr",
    "PreflightReport",
    "run_preflight_checks",
    "OpsExtractRetentionResult",
    "apply_ops_extract_retention",
    "OpsExtractOrchestrator",
    "OpsExtractOutcome",
]
