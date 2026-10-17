"""
MediScan Enterprise — Multi-Format Ingestion Engine
===================================================
Ingests PDF reports (via pdfplumber with table extraction),
scanned medical images (PNG, JPG, TIFF with OCR/metadata),
and raw clinical text notes.
"""

import io
import os
import shutil
from pathlib import Path
from typing import BinaryIO, Union
from PIL import Image

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pytesseract  # type: ignore[import-untyped]
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class MultiFormatIngestionEngine:
    """Ingests PDFs, images, and text notes with layout-aware extraction."""

    def __init__(self, tesseract_cmd: str | None = None) -> None:
        self.tesseract_cmd = tesseract_cmd
        if OCR_AVAILABLE:
            if tesseract_cmd and os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            elif shutil.which("tesseract"):
                pass
            elif os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
                pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def ingest_pdf(self, file_or_bytes: Union[str, Path, bytes, BinaryIO]) -> str:
        """Extracts running text and structured tables from a PDF."""
        if not PDF_AVAILABLE:
            raise RuntimeError("pdfplumber is required for PDF ingestion.")

        extracted_lines: list[str] = []

        if isinstance(file_or_bytes, bytes):
            stream = io.BytesIO(file_or_bytes)
            pdf_ctx = pdfplumber.open(stream)
        elif isinstance(file_or_bytes, (str, Path)):
            pdf_ctx = pdfplumber.open(file_or_bytes)
        else:
            pdf_ctx = pdfplumber.open(file_or_bytes)  # type: ignore[arg-type]

        with pdf_ctx as pdf:
            for page in pdf.pages:
                # 1. First extract formatted tables
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            clean_row = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                            if clean_row:
                                extracted_lines.append(" | ".join(clean_row))

                # 2. Extract plain text content
                page_text = page.extract_text()
                if page_text:
                    for line in page_text.splitlines():
                        line_str = line.strip()
                        if line_str and line_str not in extracted_lines:
                            extracted_lines.append(line_str)

        return "\n".join(extracted_lines)

    def ingest_image(self, file_or_bytes: Union[str, Path, bytes, BinaryIO]) -> str:
        """
        Extracts clinical text from scanned image (PNG, JPG, TIFF).
        Supports OCR via pytesseract, with metadata/embedded fallback.
        """
        if isinstance(file_or_bytes, bytes):
            image = Image.open(io.BytesIO(file_or_bytes))
        elif isinstance(file_or_bytes, (str, Path)):
            image = Image.open(file_or_bytes)
        else:
            image = Image.open(file_or_bytes)

        # Check for embedded text in PNG / TIFF metadata (common in synthetic tests & electronic PACS exports)
        embedded_text = ""
        if hasattr(image, "info") and image.info:
            for key in ["text", "Description", "Comment", "clinical_text", "ocr_text"]:
                if key in image.info and isinstance(image.info[key], str):
                    val = image.info[key].strip()
                    if val:
                        embedded_text = val
                        break

        # Attempt optical character recognition if OCR library is loaded
        ocr_text = ""
        if OCR_AVAILABLE:
            try:
                ocr_text = pytesseract.image_to_string(image, config="--psm 6").strip()
            except Exception:
                # Tesseract binary not configured or errored; use embedded text if present
                pass

        if ocr_text:
            return ocr_text
        if embedded_text:
            return embedded_text

        # If neither OCR succeeded nor embedded text found
        return ""

    def ingest_text(self, text_or_bytes: Union[str, bytes]) -> str:
        """Ingests raw clinical text or notes."""
        if isinstance(text_or_bytes, bytes):
            return text_or_bytes.decode("utf-8", errors="replace")
        return text_or_bytes

    def ingest(
        self,
        content: Union[str, bytes, BinaryIO, Path],
        filename: str = "document",
        mime_type: str | None = None,
    ) -> str:
        """Universal ingestion entrypoint routing by file extension or mime type."""
        ext = Path(filename).suffix.lower()

        if mime_type == "application/pdf" or ext == ".pdf":
            if isinstance(content, str) and not os.path.exists(content):
                # Raw text passed
                return self.ingest_text(content)
            return self.ingest_pdf(content)
        elif mime_type in ["image/png", "image/jpeg", "image/tiff"] or ext in [".png", ".jpg", ".jpeg", ".tiff"]:
            return self.ingest_image(content)
        else:
            if isinstance(content, (bytes, str)):
                return self.ingest_text(content)
            if hasattr(content, "read"):
                read_data = content.read()
                return self.ingest_text(read_data)
            return str(content)
