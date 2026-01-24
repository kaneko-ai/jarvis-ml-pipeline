"""Security Gate for JARVIS (Phase 11).

Combines Bandit, Pip-audit, AST-based banned API check, and basic secret scanning.
"""

import ast
import re
import subprocess
import sys
import os
from pathlib import Path

# Force UTF-8 encoding for stdout/stderr to handle emojis and special symbols on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# 禁止されているAPIリスト
BANNED_FUNCTIONS = {"eval", "exec", "__import__"}


def run_command(name: str, cmd: list[str]) -> bool:
    print(f"\n--- Running {name} ---")
    try:
        # We use a combined stdout/stderr for simplicity
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            # Bandit returns 1 if issues found.
            # We will handle failure logic in main() based on output if needed,
            # but for now we follow the tool's return code.
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
        else:
            print(f"✅ {name} passed.")
            # Show a snippet of output
            if result.stdout:
                lines = result.stdout.splitlines()
                print("\n".join(lines[:10]))
                if len(lines) > 10:
                    print(f"... ({len(lines)-10} more lines)")
            return True
    except FileNotFoundError:
        print(f"⚠️ {name} tool not found (cmd: {cmd[0]}). Skipping...")
        return True


def check_banned_apis(target_dirs: list[str]) -> list[str]:
    errors = []
    for d in target_dirs:
        path_dir = Path(d)
        if not path_dir.exists():
            continue
        for py_file in path_dir.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id in BANNED_FUNCTIONS:
                            errors.append(f"{py_file}:{node.lineno}: Banned function '{node.func.id}'")
                        elif (
                            isinstance(node.func, ast.Attribute) and node.func.attr in BANNED_FUNCTIONS
                        ):
                            errors.append(f"{py_file}:{node.lineno}: Banned attribute '{node.func.attr}'")
            except Exception as e:
                print(f"Error checking {py_file}: {e}")
    return errors


def scan_secrets(target_dirs: list[str]) -> list[str]:
    print("\n--- Running Custom Secret Scan ---")
    findings = []
    # Simple regex for strings that look like keys/secrets
    patterns = [
        (
            re.compile(r"(?i)(api_key|secret|token|password|auth)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
            "Potential hardcoded secret",
        ),
        (re.compile(r"['\"][a-zA-Z0-9]{32,}['\"]"), "Long hex/alphanumeric string (potential key)"),
    ]

    # Exclude certain files/patterns
    exclude_files = {".env.example", "test_", "mock_", "security_gate.py"}

    for d in target_dirs:
        path_dir = Path(d)
        if not path_dir.exists():
            continue
        for f in path_dir.rglob("*"):
            if f.is_dir() or f.suffix not in {".py", ".yml", ".json", ".js", ".html"}:
                continue
            if any(exc in f.name for exc in exclude_files):
                continue

            try:
                # Use errors='ignore' and read in chunks or handle line by line
                with open(f, "r", encoding="utf-8", errors="ignore") as content:
                    for i, line in enumerate(content, 1):
                        for pattern, msg in patterns:
                            match = pattern.search(line)
                            if match:
                                # Basic heuristic: check if it's unlikely to be a false positive
                                # (e.g. not in a comment)
                                if "#" in line and line.find("#") < line.find(match.group()):
                                    continue
                                findings.append(f"{f}:{i}: {msg}")
            except Exception as e:
                # Use str(e) and avoid printing non-encodable characters if possible
                print(f"Error scanning {f}: {str(e)[:100]}")
    return findings


def main():
    success = True
    target_dirs = ["jarvis_core", "jarvis_web", "scripts", "api"]

    # 1. Bandit
    # -lll: High severity only. We want to stop ONLY on high severity issues.
    if not run_command("Bandit", ["bandit", "-r"] + [d for d in target_dirs if os.path.exists(d)] + ["-lll"]):
        print("❌ Bandit found HIGH severity issues.")
        success = False

    # 2. Pip-audit
    req_file = "requirements.lock"
    if os.path.exists(req_file):
        if not run_command("Pip-audit", ["pip-audit", "-r", req_file]):
            success = False
    else:
        print(f"⚠️ {req_file} not found. Skipping dependency audit.")

    # 3. Banned APIs
    print("\n--- Running Banned API Check ---")
    banned_errors = check_banned_apis(target_dirs)
    if banned_errors:
        print("❌ Banned API usage found:")
        for err in banned_errors:
            print(f"  {err}")
        success = False
    else:
        print("✅ No banned API usage found.")

    # 4. Secret Scan
    secret_findings = scan_secrets(target_dirs)
    if secret_findings:
        print("❌ Potential secrets found (Review required!):")
        for find in secret_findings:
            print(f"  {find}")
        success = False
    else:
        print("✅ No potential secrets found in scanned files.")

    if not success:
        print("\n🛑 Security Gate: FAILED")
        sys.exit(1)
    else:
        print("\n🏆 Security Gate: PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
