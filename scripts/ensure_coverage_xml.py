#!/usr/bin/env python3
"""Ensure a non-empty coverage.xml exists."""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<coverage version="1.0"><packages></packages></coverage>
"""


def ensure_coverage_xml(path: Path) -> int:
    """Create a minimal coverage XML file when missing or empty."""
    if (not path.exists()) or path.stat().st_size == 0:
        path.write_text(DEFAULT_XML, encoding="utf-8")
    print(f"{path} size: {path.stat().st_size} bytes")
    return 0


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("coverage.xml")
    return ensure_coverage_xml(target)


if __name__ == "__main__":
    raise SystemExit(main())
