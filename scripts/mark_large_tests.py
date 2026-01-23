import os
from pathlib import Path

def mark_slow_tests():
    tests_dir = Path("tests")
    keywords = ["mega", "massive", "ultra", "giga", "ultimate"]
    
    for file in tests_dir.glob("test_*.py"):
        if any(kw in file.name.lower() for kw in keywords):
            content = file.read_text(encoding="utf-8")
            if "pytest.mark.slow" not in content and "pytest.mark.legacy" not in content:
                print(f"Marking {file.name} as slow...")
                # Add import if missing
                if "import pytest" not in content:
                    content = "import pytest\n" + content
                
                # Find first class or function and add marker
                if "class " in content:
                    content = content.replace("class ", "@pytest.mark.slow\nclass ", 1)
                elif "def test_" in content:
                    content = content.replace("def test_", "@pytest.mark.slow\ndef test_", 1)
                
                file.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    mark_slow_tests()
