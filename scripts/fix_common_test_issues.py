#!/usr/bin/env python3
"""Fix common test issues automatically."""

import re
from pathlib import Path
from typing import List, Tuple


def find_test_files() -> List[Path]:
    """Find all test files."""
    test_dir = Path("tests")
    return list(test_dir.rglob("test_*.py"))


def fix_missing_imports(content: str) -> Tuple[str, int]:
    """Add missing common imports."""
    fixes = 0

    # Add pytest import if missing
    if "import pytest" not in content and ("@pytest" in content or "pytest." in content):
        content = "import pytest\n" + content
        fixes += 1

    # Add unittest.mock if using Mock
    if "from unittest.mock import" not in content and (
        "MagicMock" in content or "patch" in content
    ):
        if "from unittest.mock import" not in content:
            content = "from unittest.mock import MagicMock, patch\n" + content
            fixes += 1

    return content, fixes


def fix_async_tests(content: str) -> Tuple[str, int]:
    """Fix async test issues."""
    fixes = 0

    # Add pytest.mark.asyncio to async tests
    lines = content.split("\n")
    new_lines = []

    for i, line in enumerate(lines):
        if line.strip().startswith("async def test_"):
            # Check if previous line has @pytest.mark.asyncio
            # We check the preceding lines for any decorator starting with @
            has_async_mark = False
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("@"):
                if "@pytest.mark.asyncio" in lines[j]:
                    has_async_mark = True
                    break
                j -= 1

            if not has_async_mark:
                # Find the correct indentation
                indent = line[: line.find("async def")]
                new_lines.append(f"{indent}@pytest.mark.asyncio")
                fixes += 1
        new_lines.append(line)

    return "\n".join(new_lines), fixes


def fix_network_tests(content: str) -> Tuple[str, int]:
    """Mark network-dependent tests."""
    fixes = 0

    network_patterns = [
        r"requests\.(get|post|put|delete)",
        r"httpx\.",
        r"aiohttp\.",
        r"urllib\.request",
    ]

    lines = content.split("\n")
    new_lines = []

    for i, line in enumerate(lines):
        if line.strip().startswith("def test_") or line.strip().startswith("async def test_"):
            # Look ahead to see if test uses network
            test_body = "\n".join(lines[i : i + 50])  # Check next 50 lines

            uses_network = any(re.search(p, test_body) for p in network_patterns)

            if uses_network:
                # Check if already marked
                has_network_mark = False
                j = i - 1
                while j >= 0 and lines[j].strip().startswith("@"):
                    if "@pytest.mark.network" in lines[j]:
                        has_network_mark = True
                        break
                    j -= 1

                if not has_network_mark:
                    indent = line[: line.find("def")]
                    new_lines.append(f"{indent}@pytest.mark.network")
                    fixes += 1

        new_lines.append(line)

    return "\n".join(new_lines), fixes


def fix_fixture_usage(content: str) -> Tuple[str, int]:
    """Fix common fixture usage issues."""
    fixes = 0

    # Replace direct tmp_path usage with fixture
    if "tempfile.mkdtemp()" in content:
        content = content.replace(
            "tempfile.mkdtemp()", "tmp_dir  # Use pytest tmp_dir fixture instead"
        )
        fixes += 1

    return content, fixes


def add_skip_markers(content: str) -> Tuple[str, int]:
    """Add skip markers for tests requiring external resources."""
    fixes = 0

    # Skip tests requiring specific models
    if "sentence-transformers" in content.lower() or "sentencetransformer" in content.lower():
        if (
            "try:\n    import sentence_transformers" not in content
            and "@pytest.mark.skipif" not in content
        ):
            # Add skip marker at top
            skip_marker = """
try:
    import sentence_transformers
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

"""
            if "HAS_SENTENCE_TRANSFORMERS" not in content:
                # Find first import and add after
                lines = content.split("\n")
                added = False
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        lines.insert(i, skip_marker)
                        fixes += 1
                        added = True
                        break
                if not added:
                    lines.insert(0, skip_marker)
                    fixes += 1
                content = "\n".join(lines)

    return content, fixes


def process_file(filepath: Path) -> int:
    """Process a single test file."""
    print(f"Processing {filepath}...")

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Error reading: {e}")
        return 0

    original = content
    total_fixes = 0

    # Apply fixes
    content, fixes = fix_missing_imports(content)
    total_fixes += fixes

    content, fixes = fix_async_tests(content)
    total_fixes += fixes

    content, fixes = fix_network_tests(content)
    total_fixes += fixes

    content, fixes = fix_fixture_usage(content)
    total_fixes += fixes

    content, fixes = add_skip_markers(content)
    total_fixes += fixes

    # Write back if changed
    if content != original:
        filepath.write_text(content, encoding="utf-8")
        print(f"  Applied {total_fixes} fixes")
    else:
        print("  No changes needed")

    return total_fixes


def main():
    print("=== JARVIS Test Fixer ===\n")

    test_files = find_test_files()
    print(f"Found {len(test_files)} test files\n")

    total_fixes = 0
    for filepath in test_files:
        fixes = process_file(filepath)
        total_fixes += fixes

    print("\n=== Summary ===")
    print(f"Total fixes applied: {total_fixes}")


if __name__ == "__main__":
    main()
