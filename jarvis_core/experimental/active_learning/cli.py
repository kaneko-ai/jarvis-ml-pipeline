"""CLI entry point for active learning."""

from __future__ import annotations

import argparse


def cmd_screen() -> None:
    """CLI entry point used by external dispatchers."""
    raise SystemExit(main())


def main(argv: list[str] | None = None) -> int:
    """Run the active learning CLI.

    Args:
        argv: Optional argument list.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="JARVIS Active Learning CLI")
    parser.add_argument("--version", action="store_true", help="Show version and exit.")
    args = parser.parse_args(argv)
    if args.version:
        print("active-learning 0.1.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
