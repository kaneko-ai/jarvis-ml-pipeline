from pathlib import Path
from jarvis_core.ingestion.pdf_extractor import HardenedPDFExtractor

def test_pdf_extractor_limits(tmp_path):
    # Dummy file to simulate limit check
    large_file = tmp_path / "large.pdf"
    large_file.write_bytes(b"%" * (1024 * 1024 * 2)) # 2MB dummy
    
    extractor = HardenedPDFExtractor(max_file_size_mb=1)
    text, pages, error = extractor.extract(large_file)
    
    assert error is not None
    assert error.error_code == "LIMIT_EXCEEDED"
    assert "File size" in error.message

def test_pdf_extractor_non_existent():
    extractor = HardenedPDFExtractor()
    text, pages, error = extractor.extract(Path("non_existent.pdf"))
    
    assert error is not None
    assert error.error_code == "FILE_NOT_FOUND"

def test_pdf_extractor_missing_backend(monkeypatch):
    # Force missing backends
    extractor = HardenedPDFExtractor()
    extractor._backends = {}
    
    # Create valid dummy
    dummy = Path("dummy.pdf")
    dummy.touch()
    
    text, pages, error = extractor.extract(dummy)
    assert error.error_code == "MISSING_BACKEND"
    
    dummy.unlink()
