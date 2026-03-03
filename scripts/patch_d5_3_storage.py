"""D5-3: Patch 3 CLI files to use storage_utils for log directories."""
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parent.parent


def patch_file(filepath: Path, old_lines: dict, import_line: str):
    """Replace specific lines in a file.
    
    old_lines: {line_number(1-based): (old_text_contains, new_full_line)}
    import_line: line to insert after existing imports
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Add import if not already present
    if "storage_utils" not in text:
        # Find last 'from' or 'import' line in first 30 lines
        insert_at = 0
        for i, line in enumerate(lines[:30]):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, import_line + "\n")
        print(f"  Added import at line {insert_at + 1}")
        # Shift line numbers by 1
        adjusted = {}
        for ln, val in old_lines.items():
            adjusted[ln + 1] = val
        old_lines = adjusted

    # Replace lines
    for ln, (old_contains, new_line) in old_lines.items():
        idx = ln - 1
        if idx < len(lines) and old_contains in lines[idx]:
            original = lines[idx].rstrip("\n")
            lines[idx] = new_line + "\n"
            print(f"  Line {ln}: replaced")
        else:
            # Search nearby (within 3 lines) in case import shifted things
            found = False
            for offset in range(-3, 4):
                check = idx + offset
                if 0 <= check < len(lines) and old_contains in lines[check]:
                    lines[check] = new_line + "\n"
                    print(f"  Line {check+1}: replaced (offset {offset})")
                    found = True
                    break
            if not found:
                print(f"  WARNING: Line {ln} not found for '{old_contains}'")

    filepath.write_text("".join(lines), encoding="utf-8")
    print(f"  Saved: {filepath}")


def main():
    # --- pipeline.py ---
    print("\n[1/3] Patching pipeline.py ...")
    patch_file(
        PROJECT / "jarvis_cli" / "pipeline.py",
        old_lines={
            96: (
                'Path("logs/pipeline")',
                '    log_dir = get_logs_dir("pipeline")',
            ),
            97: (
                'log_dir.mkdir',
                '    # mkdir handled by get_logs_dir',
            ),
        },
        import_line="from jarvis_core.storage_utils import get_logs_dir",
    )

    # --- orchestrate.py ---
    print("\n[2/3] Patching orchestrate.py ...")
    patch_file(
        PROJECT / "jarvis_cli" / "orchestrate.py",
        old_lines={
            432: (
                'Path("logs")',
                '    log_dir = get_logs_dir("orchestrate")',
            ),
            433: (
                'log_dir.mkdir',
                '    # mkdir handled by get_logs_dir',
            ),
        },
        import_line="from jarvis_core.storage_utils import get_logs_dir",
    )

    # --- deep_research.py ---
    print("\n[3/3] Patching deep_research.py ...")
    patch_file(
        PROJECT / "jarvis_cli" / "deep_research.py",
        old_lines={
            371: (
                'Path("logs")',
                '    log_dir = get_logs_dir("deep_research")',
            ),
            372: (
                'log_dir.mkdir',
                '    # mkdir handled by get_logs_dir',
            ),
        },
        import_line="from jarvis_core.storage_utils import get_logs_dir",
    )

    print("\n[DONE] All 3 files patched.")


if __name__ == "__main__":
    main()
