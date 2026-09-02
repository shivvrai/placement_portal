"""
Resume Parser — extract raw text from PDF and DOCX files.

Supports:
  - PDF via pdfplumber (handles multi-column, tables)
  - DOCX via python-docx
  - Plain .txt fallback
"""

import os
import io
from pathlib import Path
from typing import Union


def extract_text_from_pdf(content: bytes) -> str:
    """Extract all text from a PDF byte stream using pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    pages_text.append(text.strip())
            return "\n\n".join(pages_text)
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}") from e


def extract_text_from_docx(content: bytes) -> str:
    """Extract all paragraph text from a DOCX byte stream."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        # Also extract text from tables
        table_texts = []
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    table_texts.append(row_text)

        all_text = paragraphs + table_texts
        return "\n".join(all_text)
    except Exception as e:
        raise ValueError(f"DOCX extraction failed: {e}") from e


def extract_text_from_txt(content: bytes) -> str:
    """Decode plain text file."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file with any known encoding")


def extract_text(content: bytes, filename: str) -> str:
    """
    Dispatch to the correct parser based on file extension.

    Args:
        content: Raw file bytes
        filename: Original filename (used to detect type)

    Returns:
        Extracted plain text string
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(content)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(content)
    elif ext == ".txt":
        return extract_text_from_txt(content)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .docx, .txt")


def clean_text(raw: str) -> str:
    """
    Post-process extracted text:
    - Remove excessive whitespace / blank lines
    - Normalize unicode dashes, quotes, bullets
    """
    import re
    import unicodedata

    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", raw)

    # Replace common unicode symbols
    replacements = {
        "\u2013": "-",   # en-dash
        "\u2014": "-",   # em-dash
        "\u2022": "*",   # bullet
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\xa0": " ",     # non-breaking space
        "\t": " ",       # tabs
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_resume(content: bytes, filename: str) -> str:
    """
    Full pipeline: extract + clean.
    Returns clean plain text ready for NLP processing.
    """
    raw = extract_text(content, filename)
    return clean_text(raw)
