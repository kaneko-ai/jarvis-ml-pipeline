"""Generate Release Bundle.

Per RP-222, generates release bundle with all artifacts.
"""

from __future__ import annotations

import shutil
import json
from pathlib import Path
from datetime import datetime, timezone


def generate_release_bundle(
    version: str = "4.3",
    output_dir: str = "dist/release_bundle",
) -> None:
    """Generate release bundle.

    Args:
        version: Version string.
        output_dir: Output directory.
    """
    out_path = Path(output_dir) / f"v{version}"
    out_path.mkdir(parents=True, exist_ok=True)

    # Copy docs
    docs_to_copy = [
        "docs/README.md",
        "docs/QUICKSTART.md",
        "docs/API_REFERENCE.md",
        "docs/MASTER_SPEC.md",
        "docs/HUMAN_TASKS_PLAYBOOK_2026-02-12.md",
    ]

    for doc in docs_to_copy:
        src = Path(doc)
        if src.exists():
            shutil.copy(src, out_path / src.name)

    # Copy reports if exist
    reports = [
        "reports/eval/latest/summary.json",
        "reports/eval/latest/metrics.json",
    ]

    for report in reports:
        src = Path(report)
        if src.exists():
            shutil.copy(src, out_path / src.name)

    # Generate repro commands
    repro_content = f"""# Reproduction Commands

## Setup
```bash
git checkout v{version}
pip install -r requirements.lock
```

## Verify
```bash
python -m pytest -m core -v
python scripts/check_project_contract.py
```

## Regression
```bash
python scripts/run_regression.py --gold docs/evals/frozen_immuno_v2.jsonl
python scripts/check_quality_bar.py
```

## Benchmark
```bash
python scripts/bench.py --cases docs/evals/bench_cases.jsonl
```
"""

    (out_path / "REPRO.md").write_text(repro_content, encoding="utf-8")

    # Generate manifest
    manifest = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        "files": [f.name for f in out_path.iterdir()],
    }

    (out_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Release bundle generated: {out_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate release bundle")
    parser.add_argument("--version", type=str, default="4.3")
    parser.add_argument("--output", type=str, default="dist/release_bundle")

    args = parser.parse_args()
    generate_release_bundle(args.version, args.output)


if __name__ == "__main__":
    main()
