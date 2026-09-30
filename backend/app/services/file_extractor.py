import io
import re
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from docx import Document

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES

def validate_and_extract_file(file: UploadFile) -> Tuple[str, str, int]:
    """
    Validates file extension and size, extracts textual content,
    and returns (raw_text, file_type, file_size).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename."
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PDF (.pdf) and Word (.docx) files are supported."
        )

    # Read content
    try:
        content_bytes = file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    file_size = len(content_bytes)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 10MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes)."
        )

    # Extract text based on extension
    raw_text = ""
    file_type = ext.replace(".", "")

    if file_type == "pdf":
        raw_text = extract_text_from_pdf(content_bytes)
    elif file_type == "docx":
        raw_text = extract_text_from_docx(content_bytes)

    # Clean text
    clean_text = sanitize_extracted_text(raw_text)

    if len(clean_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract sufficient text from the resume. Please ensure the document is not an image-only scan or password protected."
        )

    return clean_text, file_type, file_size

def extract_text_from_pdf(content_bytes: bytes) -> str:
    """Extracts text from PDF bytes using pypdf."""
    try:
        stream = io.BytesIO(content_bytes)
        reader = PdfReader(stream)
        if reader.is_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Encrypted or password-protected PDF files cannot be analyzed. Please upload an unlocked PDF."
            )
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or invalid PDF file: {str(e)}"
        )

def extract_text_from_docx(content_bytes: bytes) -> str:
    """Extracts text from DOCX bytes using python-docx."""
    try:
        stream = io.BytesIO(content_bytes)
        doc = Document(stream)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())

        # Also extract text from tables if present
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))

        return "\n\n".join(text_parts)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or invalid DOCX file: {str(e)}"
        )

def sanitize_extracted_text(text: str) -> str:
    """Sanitizes raw text, removes unprintable characters, and normalizes spacing."""
    if not text:
        return ""
    # Remove null bytes and non-printable control chars except tabs/newlines
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Replace multiple blank lines with max 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Normalize excessive spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()
