"""Rule-based failure analyzer for ops_extract mode."""

from __future__ import annotations

from datetime import datetime, timezone


def classify_failure_category(error_message: str | None) -> str:
    msg = (error_message or "").lower()
    if not msg.strip():
        return "none"
    if any(token in msg for token in ["401", "403", "unauthorized", "forbidden", "auth"]):
        return "auth"
    if any(token in msg for token in ["quota", "rate limit", "too many requests"]):
        return "quota"
    if any(token in msg for token in ["timeout", "connection", "network", "dns"]):
        return "network"
    if any(token in msg for token in ["parse", "parser", "pdf", "extract"]):
        return "parser"
    if any(token in msg for token in ["ocr", "yomitoku", "tesseract"]):
        return "ocr"
    if any(token in msg for token in ["ioerror", "permission denied", "disk", "no such file"]):
        return "io"
    return "unknown"


def build_failure_analysis(
    error_message: str | None,
    *,
    status: str,
) -> dict:
    category = classify_failure_category(error_message)
    now = datetime.now(timezone.utc).isoformat()

    if category == "none":
        return {
            "status": status,
            "category": "none",
            "root_cause_guess": "",
            "recommendation_steps": [],
            "preventive_checks": [],
            "generated_at": now,
        }

    recommendations = {
        "auth": ["Validate credentials", "Refresh access token and retry"],
        "quota": ["Review current quota usage", "Retry with reduced request volume"],
        "network": ["Validate network connectivity", "Retry after short backoff"],
        "parser": ["Validate PDF integrity", "Retry with OCR path enabled"],
        "ocr": ["Validate yomitoku command availability", "Check OCR output directory permissions"],
        "io": ["Validate storage write permissions", "Check free disk space and path access"],
        "unknown": ["Review structured logs", "Inspect recent run metadata and warnings"],
    }
    checks = {
        "auth": ["check_credentials"],
        "quota": ["check_quota_limit"],
        "network": ["check_network_state"],
        "parser": ["check_pdf_extract_backend"],
        "ocr": ["check_yomitoku_available"],
        "io": ["check_storage_writable"],
        "unknown": ["check_last_run_logs"],
    }

    return {
        "status": status,
        "category": category,
        "root_cause_guess": (error_message or "").strip(),
        "recommendation_steps": recommendations.get(category, recommendations["unknown"]),
        "preventive_checks": checks.get(category, checks["unknown"]),
        "generated_at": now,
    }
