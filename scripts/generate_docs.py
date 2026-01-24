#!/usr/bin/env python3
"""Generate API documentation for JARVIS.

Creates markdown documentation from docstrings.
Per JARVIS_COMPLETION_PLAN_v3 Task 3.3
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_docstring(obj: Any) -> str:
    """Get docstring from object."""
    doc = inspect.getdoc(obj)
    return doc or ""


def get_signature(obj: Any) -> str:
    """Get function/method signature."""
    try:
        sig = inspect.signature(obj)
        return str(sig)
    except (ValueError, TypeError):
        return "()"


def document_class(cls: type) -> str:
    """Generate documentation for a class."""
    lines = []

    # Class header
    lines.append(f"### `{cls.__name__}`")
    lines.append("")

    # Docstring
    doc = get_docstring(cls)
    if doc:
        lines.append(doc)
        lines.append("")

    # Methods
    methods = []
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if not name.startswith("_") or name == "__init__":
            methods.append((name, method))

    if methods:
        lines.append("#### Methods")
        lines.append("")

        for name, method in methods:
            sig = get_signature(method)
            lines.append(f"- **`{name}{sig}`**")

            doc = get_docstring(method)
            if doc:
                # First line only
                first_line = doc.split("\n")[0]
                lines.append(f"  - {first_line}")

        lines.append("")

    return "\n".join(lines)


def document_function(func: Any) -> str:
    """Generate documentation for a function."""
    lines = []

    sig = get_signature(func)
    lines.append(f"### `{func.__name__}{sig}`")
    lines.append("")

    doc = get_docstring(func)
    if doc:
        lines.append(doc)
        lines.append("")

    return "\n".join(lines)


def document_module(module: Any) -> str:
    """Generate documentation for a module."""
    lines = []

    # Module header
    lines.append(f"## `{module.__name__}`")
    lines.append("")

    # Module docstring
    doc = get_docstring(module)
    if doc:
        lines.append(doc)
        lines.append("")

    # Classes
    classes = []
    for name, obj in inspect.getmembers(module, predicate=inspect.isclass):
        if obj.__module__ == module.__name__ and not name.startswith("_"):
            classes.append((name, obj))

    if classes:
        for name, cls in sorted(classes):
            lines.append(document_class(cls))

    # Functions
    functions = []
    for name, obj in inspect.getmembers(module, predicate=inspect.isfunction):
        if obj.__module__ == module.__name__ and not name.startswith("_"):
            functions.append((name, obj))

    if functions:
        lines.append("### Functions")
        lines.append("")
        for name, func in sorted(functions):
            lines.append(document_function(func))

    return "\n".join(lines)


def generate_api_docs(
    package_name: str = "jarvis_core",
    output_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """Generate API documentation for a package.

    Args:
        package_name: Name of package to document
        output_dir: Output directory (optional, for saving files)

    Returns:
        Dict mapping module names to documentation
    """
    docs = {}

    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        logger.error(f"Cannot import {package_name}: {e}")
        return docs

    # Generate index
    index_lines = [
        f"# {package_name} API Reference",
        "",
        "> Auto-generated documentation",
        "",
        "## Modules",
        "",
    ]

    # Find all submodules
    package_path = Path(package.__file__).parent

    for module_info in pkgutil.walk_packages([str(package_path)], prefix=f"{package_name}."):
        module_name = module_info.name

        try:
            module = importlib.import_module(module_name)
            doc = document_module(module)
            docs[module_name] = doc

            # Add to index
            short_name = module_name.replace(f"{package_name}.", "")
            index_lines.append(f"- [{short_name}](./{short_name.replace('.', '/')}.md)")

        except Exception as e:
            logger.warning(f"Cannot document {module_name}: {e}")

    # Add index
    docs["index"] = "\n".join(index_lines)

    # Save if output dir specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for name, content in docs.items():
            if name == "index":
                file_path = output_dir / "README.md"
            else:
                rel_path = name.replace(f"{package_name}.", "").replace(".", "/")
                file_path = output_dir / f"{rel_path}.md"

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"Generated: {file_path}")

    return docs


def main():
    """Generate documentation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate API documentation")
    parser.add_argument(
        "--package",
        "-p",
        default="jarvis_core",
        help="Package to document",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docs/api",
        help="Output directory",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    docs = generate_api_docs(
        package_name=args.package,
        output_dir=Path(args.output),
    )

    print(f"Generated {len(docs)} documentation files")


if __name__ == "__main__":
    main()
