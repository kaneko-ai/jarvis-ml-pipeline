"""Command-line entry point for Jarvis Core.

Provides a lightweight wrapper around `run_jarvis` so users can invoke the
core orchestration from the terminal via ``python -m jarvis_core.cli``.
"""
from argparse import ArgumentParser
from collections.abc import Sequence

from jarvis_core import run_jarvis


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and execute a Jarvis task.

    Args:
        argv: Optional list of CLI arguments. If omitted, defaults to
            ``sys.argv[1:]`` via :class:`ArgumentParser`.

    Returns:
        Exit code integer (0 on success).
    """

    parser = ArgumentParser(description="Run Jarvis Core against a textual goal.")
    parser.add_argument("goal", help="User goal to solve with Jarvis Core.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    answer = run_jarvis(args.goal)
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
