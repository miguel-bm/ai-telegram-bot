import PyPDF2
from pathlib import Path


def extract_text_from_pdf(pdf_path: Path):
    with pdf_path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        pages_text = []
        for page in reader.pages:
            pages_text.append(page.extract_text())
    return "\n\n".join(pages_text)


if __name__ == "__main__":
    pdf_path = Path("/Users/miguel/Downloads/s41586-023-05781-7.pdf")
    text = extract_text_from_pdf(pdf_path)
    print(len(text.split()))
