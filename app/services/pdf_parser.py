import io
import tempfile
import os
from pdfminer.high_level import extract_text as extract_pdf_text
from fastapi import UploadFile

async def extract_text(file: UploadFile) -> str:
    """
    Extract text from uploaded PDF file.
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        try:
            # Extract text from PDF using pdfminer (synchronous call)
            text = extract_pdf_text(tmp_path)
            return text
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")