import ast
import sys
import os
from pathlib import Path

# 禁止されているパッケージ
BANNED_IMPORTS = {"fastapi", "uvicorn", "starlette"}

def get_imports(path: Path) -> list[str]:
    imports = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            try:
                tree = ast.parse(f.read(), filename=str(path))
            except Exception:
                return []
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
    except Exception:
        pass
    return imports

def check_architecture() -> int:
    core_dir = Path("jarvis_core")
    errors = []
    
    if not core_dir.exists():
        print("jarvis_core dir missing")
        return 0

    file_count = 0
    for py_file in core_dir.rglob("*.py"):
        file_count += 1
        found_imports = get_imports(py_file)
        for imp in found_imports:
            if imp in BANNED_IMPORTS:
                errors.append((py_file.name, imp))
                
    if errors:
        print(f"FAILED: Found {len(errors)} violations in {file_count} files searched.")
        for name, imp in errors:
            # Print only filename (safe) and import name
            print(f"  Violation: {name} imports {imp}")
        return 1
    
    print(f"PASSED: Checked {file_count} files. No violations.")
    return 0

if __name__ == "__main__":
    sys.exit(check_architecture())
