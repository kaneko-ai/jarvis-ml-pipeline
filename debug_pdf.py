import fitz
import sys
from pathlib import Path
import traceback

print(f"Python: {sys.executable}")
try:
    print(f"Fitz file: {fitz.__file__}")
    print(f"Fitz version: {fitz.__version__}")
except Exception:
    print("Could not get fitz details")

pdf_path = Path("tests/fixtures/sample.pdf")
print(f"PDF Exists: {pdf_path.exists()}")

try:
    print(f"Opening: {str(pdf_path)}")
    doc = fitz.open(str(pdf_path))
    print(f"Pages: {doc.page_count}")
    for i, page in enumerate(doc):
        text = page.get_text()
        print(f"Page {i+1} text length: {len(text)}")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
