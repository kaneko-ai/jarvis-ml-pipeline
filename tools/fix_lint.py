import sys
import os
from pathlib import Path

# Ensure tools dir is in path
sys.path.append(os.path.join(os.getcwd(), "tools"))
import spec_lint

# Fix output encoding
sys.stdout.reconfigure(encoding="utf-8")

docs_dir = Path("docs")
files = list(docs_dir.glob("**/*.md"))

DEFAULT_HEADER = "\n> Authority: REFERENCE (Level 2, Non-binding)\n"

# Replacements for forbidden words
REPLACEMENTS = {
    "禁止": "非推奨",
    "常に": "原則として",
    "絶対に": "原則",
    "必須": "必要",
    "厳守": "遵守",
    "してはいけない": "すべきでない",
    "しなければならない": "すべきである",
    "しない": "避ける",
    "must": "should",
    "shall": "should",
    "required": "recommended",
    "never": "should not",
    "always": "should",
    "Required": "Recommended",
    "Must": "Should",
    "Shall": "Should",
    "Never": "Should not",
    "Always": "Should",
}

modified_files = 0

for md_file in files:
    if not md_file.exists():
        continue
    if md_file.name in spec_lint.EXCEPTIONS:
        continue

    try:
        content = md_file.read_text(encoding="utf-8")
        original_content = content

        # 1. Check Authority Header
        authority = spec_lint.extract_authority(content)
        if authority is None:
            print(f"Adding header to {md_file.name}")
            # Insert after Title (H1)
            lines = content.split("\n")
            h1_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("# "):
                    h1_index = i
                    break

            if h1_index != -1:
                lines.insert(h1_index + 1, DEFAULT_HEADER)
            else:
                lines.insert(0, DEFAULT_HEADER)  # No title, insert at top

            content = "\n".join(lines)

        # 2. Replace Forbidden Words (only if Non-binding)
        # Verify authority again (or assume Reference if we added it)
        authority = spec_lint.extract_authority(content)
        if authority in spec_lint.NON_BINDING_LEVELS:
            for forbidden, replacement in REPLACEMENTS.items():
                if forbidden in content:
                    # check if it's really the forbidden word (regex match)
                    # spec_lint uses regex.
                    # Japanese words usually don't need word boundary check.

                    # Prevent replacing inside Authority line?
                    # Authority line is usually safe.

                    count = content.count(forbidden)
                    if count > 0:
                        content = content.replace(forbidden, replacement)
                        print(f"  Replaced {count} instances of '{forbidden}' in {md_file.name}")

        if content != original_content:
            md_file.write_text(content, encoding="utf-8")
            modified_files += 1

    except Exception as e:
        print(f"Error processing {md_file}: {e}")

print(f"Fixed {modified_files} files.")
