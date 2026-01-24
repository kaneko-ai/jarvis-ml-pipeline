import pytest
import os
from pathlib import Path
from jarvis_core.security.path_validator import PathValidator, ForbiddenPathError


def test_path_validator_basic(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    validator = PathValidator(base_dir=base_dir)

    # Valid path
    safe_file = base_dir / "safe.txt"
    safe_file.touch()
    assert validator.validate(safe_file) == safe_file.resolve()

    # Subdir
    sub_dir = base_dir / "subdir"
    sub_dir.mkdir()
    sub_file = sub_dir / "subsafe.txt"
    sub_file.touch()
    assert validator.validate(sub_file) == sub_file.resolve()


def test_path_validator_traversal(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    outside_file = tmp_path / "outside.txt"
    outside_file.touch()

    validator = PathValidator(base_dir=base_dir)

    # Absolute path outside
    with pytest.raises(ForbiddenPathError, match="is outside allowed base"):
        validator.validate(outside_file)

    # Relative with ..
    # Note: Path("a/../b") does NOT automatically normalize unless resolve() is called
    # But my validator checks path.parts
    with pytest.raises(ForbiddenPathError, match="contains '..' traversal pattern"):
        validator.validate(base_dir / ".." / "outside.txt")


def test_path_validator_extensions(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    validator = PathValidator(base_dir=base_dir, allowed_extensions={".pdf", ".bib"})

    pdf_file = base_dir / "test.pdf"
    pdf_file.touch()
    assert validator.validate(pdf_file) == pdf_file.resolve()

    bib_file = base_dir / "test.BIB"  # Case insensitive
    bib_file.touch()
    assert validator.validate(bib_file) == bib_file.resolve()

    txt_file = base_dir / "test.txt"
    txt_file.touch()
    with pytest.raises(ForbiddenPathError, match="Extension .txt not allowed"):
        validator.validate(txt_file)


def test_path_validator_symlinks(tmp_path):
    base_dir = (tmp_path / "base").resolve()
    base_dir.mkdir()

    outside_dir = (tmp_path / "outside").resolve()
    outside_dir.mkdir()
    outside_file = outside_dir / "secret.txt"
    outside_file.touch()

    validator = PathValidator(base_dir=base_dir, allow_symlinks=False)

    link_path = base_dir / "link_to_outside"
    try:
        # Windows requires special privileges for symlinks sometimes
        os.symlink(outside_dir, link_path, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks not supported or permitted in this environment")

    # Accessing via symlink should be caught even if resolved path is technically outside base
    # (Because resolve() follows symlinks, and the startswith check fails)
    # AND our explicit symlink check catches it if it exists.
    with pytest.raises(ForbiddenPathError, match="Symlinks are restricted"):
        validator.validate(link_path / "secret.txt")


def test_path_validator_case_insensitivity(tmp_path):
    # This might depend on OS but we can test the extension set logic
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    validator = PathValidator(base_dir=base_dir, allowed_extensions={"PDF"})
    assert ".pdf" in validator.allowed_extensions

    target = base_dir / "doc.pdf"
    target.touch()
    assert validator.validate(target) == target.resolve()
