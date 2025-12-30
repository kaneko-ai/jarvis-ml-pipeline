from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_ui_contract_audit_script() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "audit_ui_contract.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"audit_ui_contract.py failed with {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
