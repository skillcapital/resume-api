import io
import tempfile
import os
import asyncio
from fastapi import UploadFile

# Lazy import to reduce cold start time
def _get_pdf_extractor():
    """Lazy import pdfminer only when needed."""
    from pdfminer.high_level import extract_text as extract_pdf_text
    return extract_pdf_text

async def extract_text(file: UploadFile) -> str:
    """
    Extract text from uploaded PDF file.
    Uses async executor to avoid blocking the event loop.
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        try:
            # Run blocking PDF extraction in thread pool to avoid blocking event loop
            extract_pdf_text = _get_pdf_extractor()
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, extract_pdf_text, tmp_path)
            return text
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass  # Ignore cleanup errors
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")