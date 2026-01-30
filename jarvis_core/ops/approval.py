"""Approval System (Phase 2-ΩΩ).

Manages human approval workflow for research outputs before external sharing.
"""

import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_approval(
    run_dir: Path, approved: bool, approver: str, scope: str, notes: str = ""
) -> Path:
    """Write approval status.

    Args:
        run_dir: Path to run directory
        approved: Approval status
        approver: Name of approver
        scope: Scope of approval (e.g., "publication", "internal")
        notes: Optional notes

    Returns:
        Path to approval.json
    """
    approval = {
        "approved": approved,
        "approver": approver,
        "scope": scope,
        "timestamp": datetime.datetime.now().isoformat(),
        "notes": notes,
    }

    approval_path = run_dir / "approval.json"

    with open(approval_path, "w", encoding="utf-8") as f:
        json.dump(approval, f, indent=2, ensure_ascii=False)

    logger.info(f"Approval {'granted' if approved else 'revoked'} by {approver}")

    return approval_path


def check_approval(run_dir: Path) -> bool:
    """Check if run is approved for export/sharing.

    Args:
        run_dir: Path to run directory

    Returns:
        True if approved
    """
    approval_path = run_dir / "approval.json"

    if not approval_path.exists():
        return False

    with open(approval_path, encoding="utf-8") as f:
        approval = json.load(f)

    return approval.get("approved", False)


def require_approval(run_dir: Path, operation: str = "export"):
    """Require approval or raise error.

    Args:
        run_dir: Path to run directory
        operation: Operation name (for error message)

    Raises:
        PermissionError: If not approved
    """
    if not check_approval(run_dir):
        raise PermissionError(
            f"Run {run_dir.name} not approved for {operation}. "
            f"Use 'jarvis_cli approve' to grant approval."
        )
