"""Generate a sample PDF fixture for tests."""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "tests" / "fixtures" / "sample.pdf"


def generate_pdf(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    for page_number in range(1, 4):
        pdf.setFont("Helvetica", 16)
        pdf.drawString(72, height - 72, f"Page {page_number}")
        pdf.showPage()

    pdf.save()


if __name__ == "__main__":
    generate_pdf(OUTPUT_PATH)
