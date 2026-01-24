import os
import re

def fix_e402(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    docstring = []
    imports = []
    others = []
    
    i = 0
    # Collect docstring if it exists at the top
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if not others:
                docstring.append(line)
                i += 1
                continue
            else:
                others.append(line)
                i += 1
                continue
        
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not others:
                quote = '"""' if stripped.startswith('"""') else "'''"
                docstring.append(line)
                if stripped.count(quote) == 1:
                    i += 1
                    while i < len(lines) and quote not in lines[i]:
                        docstring.append(lines[i])
                        i += 1
                    if i < len(lines):
                        docstring.append(lines[i])
                i += 1
                continue
        
        break
    
    # Process the rest
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        is_top_level_import = (line.startswith("import ") or line.startswith("from ")) and not line.startswith(" ") and not line.startswith("\t")
        
        if is_top_level_import:
            # Multi-line import check (parentheses)
            imports.append(line)
            if "(" in line and ")" not in line:
                i += 1
                while i < len(lines) and ")" not in lines[i]:
                    imports.append(lines[i])
                    i += 1
                if i < len(lines):
                    imports.append(lines[i])
        else:
            others.append(line)
        i += 1

    # Re-order
    # Check for __future__
    future_imports = [imp for imp in imports if "from __future__" in imp]
    regular_imports = [imp for imp in imports if "from __future__" not in imp]
    
    new_content = "".join(docstring) + "".join(future_imports) + "".join(regular_imports) + "".join(others)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    with open("e402_violations_refined.txt", "r", encoding="utf-8") as f:
        files_to_fix = set()
        for line in f:
            if ":" in line:
                files_to_fix.add(line.split(":")[0])
    
    for path in files_to_fix:
        if os.path.exists(path):
            print(f"Fixing {path}")
            fix_e402(path)
