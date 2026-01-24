import pytest
import zipfile
from jarvis_core.security.fs_safety import sanitize_filename, resolve_under, safe_extract_zip


def test_sanitize_filename():
    assert sanitize_filename("safe.pdf") == "safe.pdf"
    assert sanitize_filename("../../hidden.txt") == ".._.._hidden.txt"
    assert sanitize_filename("file\x00name.pdf") == "file_name.pdf"
    assert sanitize_filename("   spaced name.pdf   ") == "spaced name.pdf"

    long_input = "long" * 100 + ".pdf"
    assert sanitize_filename(long_input) == ("long" * 100)[:110] + ".pdf"

    assert sanitize_filename("") == "unnamed_file"


def test_resolve_under(tmp_path):
    base = tmp_path / "base"
    base.mkdir()

    # Safe path
    target = base / "file.txt"
    assert resolve_under(base, target) == target.resolve()

    # Unsafe path (traversal)
    unsafe = base / ".." / "outside.txt"
    with pytest.raises(ValueError, match="not under"):
        resolve_under(base, unsafe)


def test_safe_extract_zip(tmp_path):
    zip_dir = tmp_path / "zips"
    zip_dir.mkdir()
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # 1. Create a safe zip
    zip_path = zip_dir / "safe.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file1.pdf", "content1")
        zf.writestr("dir/file2.pdf", "content2")

    extracted = safe_extract_zip(zip_path, dest_dir, allowed_ext={".pdf"})
    assert len(extracted) == 2
    assert (dest_dir / "file1.pdf").exists()
    assert (dest_dir / "dir/file2.pdf").exists()

    # 2. Zip Slip attempt
    slip_zip = zip_dir / "slip.zip"
    with zipfile.ZipFile(slip_zip, "w") as zf:
        # Construct a manually crafted zip entry with traversal
        zf.writestr("../evil.txt", "evil")

    with pytest.raises(ValueError, match="Zip Slip attempt detected"):
        safe_extract_zip(slip_zip, dest_dir)

    # 3. File count limit
    limit_zip = zip_dir / "limit.zip"
    with zipfile.ZipFile(limit_zip, "w") as zf:
        zf.writestr("f1.txt", "c")
        zf.writestr("f2.txt", "c")

    with pytest.raises(ValueError, match="Too many files"):
        safe_extract_zip(limit_zip, dest_dir, max_files=1)

    # 4. Total size limit
    size_zip = zip_dir / "size.zip"
    with zipfile.ZipFile(size_zip, "w") as zf:
        zf.writestr("large.txt", "x" * 1000)

    with pytest.raises(ValueError, match="Total extracted size exceeds"):
        safe_extract_zip(size_zip, dest_dir, max_total_size=500)
