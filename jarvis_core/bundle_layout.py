"""Bundle Layout Contract.

Per V4-P04, this defines and validates output directory structure.
"""
from __future__ import annotations

from pathlib import Path
from typing import List


# Required files in Bundle v2
REQUIRED_FILES = [
    "bundle.json",
    "audit.md",
]

# Optional directories
OPTIONAL_DIRS = [
    "evidence",
    "vectors",
    "workflows",
]


class BundleLayout:
    """Bundle v2 layout validator."""

    def __init__(self, path: str):
        self.path = Path(path)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate bundle layout.

        Returns:
            Tuple of (is_valid, list of issues).
        """
        issues = []

        if not self.path.exists():
            return False, ["Bundle directory does not exist"]

        if not self.path.is_dir():
            return False, ["Bundle path is not a directory"]

        # Check required files
        for req_file in REQUIRED_FILES:
            if not (self.path / req_file).exists():
                issues.append(f"Missing required file: {req_file}")

        return len(issues) == 0, issues

    def get_structure(self) -> dict:
        """Get bundle structure as dict."""
        structure = {
            "path": str(self.path),
            "files": [],
            "directories": [],
        }

        if self.path.exists():
            for item in self.path.iterdir():
                if item.is_file():
                    structure["files"].append(item.name)
                elif item.is_dir():
                    structure["directories"].append(item.name)

        return structure


def validate_bundle_layout(path: str) -> tuple[bool, List[str]]:
    """Validate bundle layout at path."""
    layout = BundleLayout(path)
    return layout.validate()


def ensure_bundle_structure(path: str) -> None:
    """Ensure bundle directory structure exists."""
    bundle_path = Path(path)
    bundle_path.mkdir(parents=True, exist_ok=True)

    for opt_dir in OPTIONAL_DIRS:
        (bundle_path / opt_dir).mkdir(exist_ok=True)
