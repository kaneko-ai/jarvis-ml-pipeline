"""Ops+Extract mode components.

This package provides an LLM-independent extraction flow focused on
operational robustness and PDF text recovery quality.
"""

from .contracts import (
    OPS_EXTRACT_OPTIONAL_ARTIFACTS,
    OPS_EXTRACT_SCHEMA_VERSION,
    OPS_EXTRACT_SYNC_STATE_VERSION,
    OPS_EXTRACT_VERSION,
    OpsExtractConfig,
    OpsExtractThresholds,
    build_ops_extract_config,
)
from .drive_client import DriveResumableClient, DriveUploadError
from .drive_repair import plan_duplicate_folder_repair, repair_duplicate_folders
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
from .network import detect_network_profile
from .oauth_google import refresh_access_token, resolve_drive_access_token
from .orchestrator import OpsExtractOrchestrator, OpsExtractOutcome
from .pdf_diagnosis import PdfDiagnosis, diagnose_pdf, diagnose_pdfs
from .preflight import PreflightReport, run_preflight_checks
from .retention import OpsExtractRetentionResult, apply_ops_extract_retention
from .runbook import generate_runbook
from .schema_validate import (
    SchemaValidationError,
    validate_contract_path,
    validate_payload,
    validate_run_contracts,
)
from .stage_cache import (
    STAGE_CACHE_VERSION,
    cache_outputs_match,
    compute_input_hash,
    load_stage_cache,
    save_stage_cache,
    update_stage_cache_entry,
)
from .sync_queue import enqueue_sync_request, load_sync_queue, mark_sync_queue_state
from .doctor import run_doctor
from .scoreboard import (
    compute_extract_score,
    compute_ops_score,
    detect_anomalies,
    generate_weekly_report,
)

__all__ = [
    "OPS_EXTRACT_OPTIONAL_ARTIFACTS",
    "OPS_EXTRACT_SCHEMA_VERSION",
    "OPS_EXTRACT_SYNC_STATE_VERSION",
    "OPS_EXTRACT_VERSION",
    "OpsExtractThresholds",
    "OpsExtractConfig",
    "build_ops_extract_config",
    "classify_failure_category",
    "build_failure_analysis",
    "DriveResumableClient",
    "DriveUploadError",
    "plan_duplicate_folder_repair",
    "repair_duplicate_folders",
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
    "detect_network_profile",
    "refresh_access_token",
    "resolve_drive_access_token",
    "PdfDiagnosis",
    "diagnose_pdf",
    "diagnose_pdfs",
    "PreflightReport",
    "run_preflight_checks",
    "OpsExtractRetentionResult",
    "apply_ops_extract_retention",
    "generate_runbook",
    "SchemaValidationError",
    "validate_payload",
    "validate_contract_path",
    "validate_run_contracts",
    "STAGE_CACHE_VERSION",
    "compute_input_hash",
    "load_stage_cache",
    "save_stage_cache",
    "cache_outputs_match",
    "update_stage_cache_entry",
    "enqueue_sync_request",
    "load_sync_queue",
    "mark_sync_queue_state",
    "run_doctor",
    "compute_ops_score",
    "compute_extract_score",
    "detect_anomalies",
    "generate_weekly_report",
    "OpsExtractOrchestrator",
    "OpsExtractOutcome",
]
