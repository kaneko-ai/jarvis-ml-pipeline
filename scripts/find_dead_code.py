#!/usr/bin/env python
"""未使用コード検出スクリプト"""
import subprocess
import sys


def main():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vulture",
            "jarvis_core",
            "vulture_whitelist.py",
            "--min-confidence",
            "80",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
