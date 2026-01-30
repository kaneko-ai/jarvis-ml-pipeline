import os
import tempfile
from pathlib import Path
from scripts.arch_gate import get_imports, BANNED_IMPORTS


def test_arch_gate_detection():
    """Verify that banned imports are indeed detected."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write("import fastapi\nfrom uvicorn import run\nimport os\n")
        tmp_path = Path(tmp.name)

    try:
        imports = get_imports(tmp_path)
        assert "fastapi" in imports
        assert "uvicorn" in imports
        assert "os" in imports

        banned_found = [i for i in imports if i in BANNED_IMPORTS]
        assert len(banned_found) == 2
    finally:
        os.unlink(tmp_path)


def test_arch_gate_clean_file():
    """Verify that clean files don't trigger violations."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write("import os\nimport sys\nfrom pathlib import Path\n")
        tmp_path = Path(tmp.name)

    try:
        imports = get_imports(tmp_path)
        banned_found = [i for i in imports if i in BANNED_IMPORTS]
        assert len(banned_found) == 0
    finally:
        os.unlink(tmp_path)