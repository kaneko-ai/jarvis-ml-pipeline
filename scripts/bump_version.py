"""Bump pyproject.toml version to 2.0.0."""
from pathlib import Path

p = Path("pyproject.toml")
text = p.read_text(encoding="utf-8")
text = text.replace('version = "1.0.0"', 'version = "2.0.0"', 1)
p.write_text(text, encoding="utf-8")
print("pyproject.toml updated to v2.0.0")

# Verify
for line in p.read_text(encoding="utf-8").splitlines():
    if "version" in line and "2.0.0" in line:
        print(f"Confirmed: {line.strip()}")
        break
