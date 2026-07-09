"""
LegalDocAI - PDF Text Extractor
Extracts clean text from legal PDFs using PyMuPDF (primary) and pdfplumber (fallback for tables).
"""

import re
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ExtractedPage:
    """Represents extracted text from a single PDF page."""
    page_number: int
    text: str
    has_table: bool = False


@dataclass
class ExtractedDocument:
    """Represents extracted text from a full PDF document."""
    filename: str
    total_pages: int
    pages: list  # list of ExtractedPage
    full_text: str


def clean_text(text: str) -> str:
    """Clean extracted text - remove extra whitespace, fix encoding issues."""
    if not text:
        return ""

    # Fix common PDF extraction issues
    text = text.replace("\xa0", " ")       # non-breaking space
    text = text.replace("\u2018", "'")      # left single quote
    text = text.replace("\u2019", "'")      # right single quote
    text = text.replace("\u201c", '"')      # left double quote
    text = text.replace("\u201d", '"')      # right double quote
    text = text.replace("\u2014", "—")      # em dash
    text = text.replace("\u2013", "–")      # en dash

    # Remove excessive newlines (keep max 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove excessive spaces (keep max 1)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Remove page headers/footers patterns common in legal docs
    # e.g., "Page 1 of 50", "THE CONSTITUTION OF INDIA" repeated headers
    text = re.sub(r"(?i)page\s+\d+\s+of\s+\d+", "", text)

    return text.strip()


def extract_with_pymupdf(pdf_path: Path) -> ExtractedDocument:
    """
    Extract text using PyMuPDF (fitz) - fast and reliable for text-based PDFs.
    """
    doc = fitz.open(str(pdf_path))
    pages = []
    all_text_parts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        cleaned = clean_text(text)

        if cleaned:
            extracted_page = ExtractedPage(
                page_number=page_num + 1,
                text=cleaned
            )
            pages.append(extracted_page)
            all_text_parts.append(cleaned)

    total_pages = len(doc) if hasattr(doc, '__len__') else len(pages)
    doc.close()

    return ExtractedDocument(
        filename=pdf_path.name,
        total_pages=total_pages,
        pages=pages,
        full_text="\n\n".join(all_text_parts)
    )


def extract_with_pdfplumber(pdf_path: Path) -> ExtractedDocument:
    """
    Extract text using pdfplumber - better for tables and structured layouts.
    Used as fallback or for table-heavy documents.
    """
    pages = []
    all_text_parts = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            cleaned = clean_text(text)

            # Check for tables
            tables = page.extract_tables()
            has_table = len(tables) > 0

            # If tables exist, format them as text
            if tables:
                for table in tables:
                    table_text = "\n".join(
                        " | ".join(str(cell or "") for cell in row)
                        for row in table
                    )
                    cleaned += "\n\n[TABLE]\n" + table_text + "\n[/TABLE]\n"

            if cleaned:
                extracted_page = ExtractedPage(
                    page_number=page_num + 1,
                    text=cleaned,
                    has_table=has_table
                )
                pages.append(extracted_page)
                all_text_parts.append(cleaned)

    return ExtractedDocument(
        filename=pdf_path.name,
        total_pages=total_pages,
        pages=pages,
        full_text="\n\n".join(all_text_parts)
    )


def extract_text_from_pdf(pdf_path: Path, use_pdfplumber: bool = False) -> ExtractedDocument:
    """
    Main extraction function. Uses PyMuPDF by default, falls back to pdfplumber.

    Args:
        pdf_path: Path to the PDF file
        use_pdfplumber: Force using pdfplumber (for table-heavy docs)

    Returns:
        ExtractedDocument with all pages and full text
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not pdf_path.suffix.lower() == ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    print(f"  📖 Extracting text from: {pdf_path.name}")

    if use_pdfplumber:
        result = extract_with_pdfplumber(pdf_path)
    else:
        # Try PyMuPDF first
        result = extract_with_pymupdf(pdf_path)

        # If very little text extracted, fallback to pdfplumber (might be scanned)
        if len(result.full_text) < 100:
            print(f"  ⚠️  PyMuPDF got very little text, trying pdfplumber...")
            result = extract_with_pdfplumber(pdf_path)

    # Final check
    if len(result.full_text) < 100:
        print(f"  ❌ Warning: Very little text extracted from {pdf_path.name}")
        print(f"     This might be a scanned/image PDF. OCR may be needed.")
    else:
        print(f"  ✅ Extracted {len(result.pages)} pages, {len(result.full_text):,} characters")

    return result


def save_extracted_text(doc: ExtractedDocument, output_dir: Path) -> Path:
    """Save extracted text to a .txt file for inspection."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{Path(doc.filename).stem}.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc.full_text)

    print(f"  💾 Saved extracted text to: {output_path.name}")
    return output_path


if __name__ == "__main__":
    # Quick test - extract from a sample PDF
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

    for pdf_file in RAW_DATA_DIR.glob("*.pdf"):
        print(f"\n{'='*60}")
        doc = extract_text_from_pdf(pdf_file)
        save_extracted_text(doc, PROCESSED_DATA_DIR)
