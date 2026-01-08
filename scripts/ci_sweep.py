#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, List, Optional


FILE_LINE_RE = re.compile(r'File "([^"]+)", line \d+')


def discover_test_files(root: Path) -> List[Path]:
    return sorted(root.glob("test_*.py"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_pytest(test_file: Path, report_path: Path) -> int:
    cmd = [
        "pytest",
        str(test_file),
        "--json-report",
        f"--json-report-file={report_path}",
    ]
    result = subprocess.run(cmd, check=False)
    return result.returncode


def first_failure_phase(test: dict[str, Any]) -> Optional[tuple[str, dict[str, Any]]]:
    for phase in ("setup", "call", "teardown"):
        phase_data = test.get(phase)
        if not isinstance(phase_data, dict):
            continue
        if phase_data.get("outcome") in {"failed", "error"}:
            return phase, phase_data
    return None


def extract_message(phase_data: dict[str, Any]) -> str:
    crash = phase_data.get("crash")
    if isinstance(crash, dict):
        message = crash.get("message")
        if message:
            return message

    for key in ("longreprtext", "longrepr", "message"):
        value = phase_data.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, dict):
            nested_message = value.get("message") or value.get("reprcrash")
            if isinstance(nested_message, str) and nested_message.strip():
                return nested_message
    return ""


def extract_files(text: str) -> List[str]:
    files: List[str] = []
    for match in FILE_LINE_RE.finditer(text):
        files.append(match.group(1))
    return files


def collect_failures(report: dict[str, Any]) -> List[dict[str, Any]]:
    failures: List[dict[str, Any]] = []
    for test in report.get("tests", []):
        if not isinstance(test, dict):
            continue
        failure = first_failure_phase(test)
        if not failure:
            continue
        _, phase_data = failure
        message_text = extract_message(phase_data)
        message_lines = [line for line in message_text.splitlines() if line.strip()]
        message_excerpt = "\n".join(message_lines[:3])
        related_files = set()
        if isinstance(phase_data.get("crash"), dict):
            crash_path = phase_data["crash"].get("path")
            if crash_path:
                related_files.add(crash_path)
        related_files.update(extract_files(message_text))
        failures.append(
            {
                "nodeid": test.get("nodeid", "<unknown>"),
                "outcome": phase_data.get("outcome", "failed"),
                "message": message_excerpt or "<no message>",
                "files": sorted(related_files),
            }
        )
    return failures


def write_failures_md(output_path: Path, failures: Iterable[dict[str, Any]]) -> None:
    failures = list(failures)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("# CI Sweep Failures\n\n")
        if not failures:
            handle.write("No failures found.\n")
            return
        handle.write("| nodeid | outcome | message | related files |\n")
        handle.write("| --- | --- | --- | --- |\n")
        for failure in failures:
            message = failure["message"].replace("\n", "<br>")
            files = "<br>".join(failure["files"]) if failure["files"] else ""
            handle.write(
                f"| {failure['nodeid']} | {failure['outcome']} | {message} | {files} |\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest in shards and collect failures.")
    parser.add_argument(
        "--tests-root",
        default="tests",
        help="Directory containing test_*.py files (default: tests).",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts/ci",
        help="Directory to write json reports and failures.md (default: artifacts/ci).",
    )
    args = parser.parse_args()

    tests_root = Path(args.tests_root)
    artifacts_dir = Path(args.artifacts_dir)
    ensure_dir(artifacts_dir)

    test_files = discover_test_files(tests_root)
    if not test_files:
        print(f"No test files found under {tests_root}.")

    all_failures: List[dict[str, Any]] = []
    for index, test_file in enumerate(test_files, start=1):
        report_path = artifacts_dir / f"report_{index}_{test_file.stem}.json"
        run_pytest(test_file, report_path)
        if not report_path.exists():
            all_failures.append(
                {
                    "nodeid": f"{test_file} (report missing)",
                    "outcome": "error",
                    "message": "pytest did not generate a json report",
                    "files": [str(test_file)],
                }
            )
            continue
        try:
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            all_failures.append(
                {
                    "nodeid": f"{test_file} (report invalid)",
                    "outcome": "error",
                    "message": "pytest json report could not be parsed",
                    "files": [str(test_file)],
                }
            )
            continue
        all_failures.extend(collect_failures(report_data))

    failures_md = artifacts_dir / "failures.md"
    write_failures_md(failures_md, all_failures)
    print(f"Wrote {failures_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
