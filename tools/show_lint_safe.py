import sys
import spec_lint
from pathlib import Path

# Fix formatting for console output if needed
sys.stdout.reconfigure(encoding="utf-8")

docs_dir = Path("docs")
files = list(docs_dir.glob("**/*.md"))
all_violations = []

for md_file in files:
    if not md_file.exists():
        continue
    try:
        violations = spec_lint.check_file(md_file)
        all_violations.extend(violations)
    except Exception as e:
        print(f"Error checking {md_file}: {e}")

print(f"Total violations: {len(all_violations)}")
for v in all_violations:
    # Print simpler format
    print(f"{v.file}|{v.line}|{v.word}")
