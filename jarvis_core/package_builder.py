"""Package builder compatibility shim."""

from __future__ import annotations

from jarvis_core.submission.package_builder import (
    SubmissionResult,
    build_submission_package,
    is_ready_to_submit,
)

__all__ = ["SubmissionResult", "build_submission_package", "is_ready_to_submit"]
