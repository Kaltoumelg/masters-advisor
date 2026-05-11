import fitz


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from uploaded PDF CV bytes.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        return "\n".join(text_parts).strip()

    except Exception as e:
        return f"Could not extract CV text: {str(e)}"