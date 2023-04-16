import PyPDF2
from pathlib import Path


def extract_text_from_pdf(pdf_path: Path):
    with pdf_path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        pages_text = []
        for page in reader.pages:
            pages_text.append(page.extract_text())
    return "\n\n".join(pages_text)
