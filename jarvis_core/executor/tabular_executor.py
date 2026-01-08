"""
Jarvis Tabular Task Executor

Jarvisからtabular pipelineを実行
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TabularTaskExecutor:
    """Tabular Pipeline Executor.
    
    Jarvisの責務:
    - configを渡す
    - run_idを払い出す
    - 実行ログを集約する
    
    データ内容の理解はtabular pipeline側の責務。
    """

    def __init__(self, python_path: str | None = None):
        """初期化."""
        self.python_path = python_path or sys.executable

    def execute(
        self,
        config_path: str,
        timeout: int = 600,
    ) -> dict[str, Any]:
        """
        タスクを実行.
        
        Args:
            config_path: 設定ファイルパス
            timeout: タイムアウト秒数
        
        Returns:
            実行結果
        """
        cmd = [
            self.python_path,
            "-m", "cli.tabular_run",
            "--config", config_path,
        ]

        logger.info(f"Executing: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(Path(__file__).parent.parent),
            )

            success = result.returncode == 0

            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "config_path": config_path,
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Task timed out after {timeout}s")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Timeout after {timeout}s",
                "config_path": config_path,
            }

        except Exception as e:
            logger.error(f"Task failed: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "config_path": config_path,
            }

    def list_runs(self, runs_dir: str = "runs") -> list:
        """実行履歴を一覧."""
        runs = sorted(Path(runs_dir).glob("*"))
        return [str(r.name) for r in runs if r.is_dir()]
