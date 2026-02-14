from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_audit_repo_state_runs() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "audit_repo_state.py"
    result = subprocess.run([sys.executable, str(script)], cwd=root, check=False)
    assert result.returncode == 0
    report = root / "reports" / "audit_repo_state.md"
    assert report.exists()
