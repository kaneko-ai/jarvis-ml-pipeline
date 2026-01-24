import os
import re

def find_e402_violations(directory):
    violations = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    found_code = False
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        stripped = line.strip()
                        
                        if not stripped or stripped.startswith("#"):
                            i += 1
                            continue
                        
                        # Skip indented lines (not top-level)
                        if line.startswith(" ") or line.startswith("\t"):
                            found_code = True # Indented code is still code
                            i += 1
                            continue

                        # Check if it's a docstring start/end
                        if stripped.startswith('"""') or stripped.startswith("'''"):
                            if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                                # Multi-line
                                quote = '"""' if stripped.startswith('"""') else "'''"
                                i += 1
                                while i < len(lines) and quote not in lines[i]:
                                    i += 1
                            i += 1 
                            continue
                            
                        is_import = stripped.startswith("import ") or stripped.startswith("from ")
                        
                        if is_import:
                            if found_code:
                                violations.append(f"{path}:{i+1}: Import after code: {stripped}")
                        else:
                            found_code = True
                        i += 1

                            
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    return violations

if __name__ == "__main__":
    v = find_e402_violations("tests")
    with open("e402_violations_refined.txt", "w", encoding="utf-8") as out:
        for item in v:
            out.write(item + "\n")
    print(f"Found {len(v)} top-level violations.")


