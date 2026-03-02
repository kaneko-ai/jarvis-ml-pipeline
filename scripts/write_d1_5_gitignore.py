import pathlib

gi_path = pathlib.Path(".gitignore")
content = gi_path.read_text(encoding="utf-8") if gi_path.exists() else ""

additions = """
# --- D1-5: Temp build scripts ---
/write_*.py
/fix_*.py
/check_*.py
/tatus
/mcp_test_params.json
"""

if "/write_*.py" not in content:
    new_content = content.rstrip() + "\n" + additions
    gi_path.write_text(new_content, encoding="utf-8")
    print(f"Updated .gitignore: added temp file patterns")
else:
    print(".gitignore already has patterns")
