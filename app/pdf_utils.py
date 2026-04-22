import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {str(e)}")

    if not text_parts:
        raise ValueError("No readable text found in the PDF. It may be scanned or image-only.")

    return "\n\n".join(text_parts)
