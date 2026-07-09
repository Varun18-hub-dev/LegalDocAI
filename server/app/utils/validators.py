from app.utils.exceptions import UnsupportedFileType, InvalidDocument

def validate_pdf_file(filename: str) -> None:
    """Ensure the uploaded file is a PDF."""
    if not filename.lower().endswith(".pdf"):
        raise UnsupportedFileType("Invalid file extension. Only PDF uploads are supported.")

def validate_query_text(question: str) -> None:
    """Ensure the user query is non-empty and valid."""
    if not question or not question.strip():
        raise InvalidDocument("Query question cannot be empty or whitespace.")
