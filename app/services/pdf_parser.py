import io
import tempfile
import os
import asyncio
import time
from fastapi import UploadFile

# Lazy import to reduce cold start time
def _get_pdf_extractor():
    """Lazy import pdfminer only when needed."""
    from pdfminer.high_level import extract_text as extract_pdf_text
    return extract_pdf_text

def _safe_delete_file(file_path: str, max_retries: int = 3, delay: float = 0.1) -> None:
    """
    Safely delete a file with retry logic to handle file lock issues.
    
    Args:
        file_path: Path to the file to delete
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    if not os.path.exists(file_path):
        return
    
    for attempt in range(max_retries):
        try:
            # On Windows, ensure file is not read-only
            if os.name == 'nt':
                os.chmod(file_path, 0o777)
            os.unlink(file_path)
            return  # Successfully deleted
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                # Wait a bit before retrying to allow file handles to be released
                time.sleep(delay * (attempt + 1))
            else:
                # Last attempt failed, log but don't raise
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not delete temporary file {file_path} after {max_retries} attempts: {str(e)}")

async def extract_text(file: UploadFile) -> str:
    """
    Extract text from uploaded PDF file.
    Uses async executor to avoid blocking the event loop.
    """
    tmp_path = None
    try:
        # Read file content
        contents = await file.read()
        
        # Create temporary file and ensure it's fully written and closed
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(contents)
            tmp_file.flush()  # Ensure all data is written
            os.fsync(tmp_file.fileno())  # Force write to disk
            tmp_path = tmp_file.name
        
        # Ensure file handle is fully closed before extraction
        # Small delay to ensure file system has released the handle
        await asyncio.sleep(0.01)
        
        # Run blocking PDF extraction in thread pool to avoid blocking event loop
        extract_pdf_text = _get_pdf_extractor()
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, extract_pdf_text, tmp_path)
        
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")
    finally:
        # Clean up temporary file with retry logic
        if tmp_path:
            # Run deletion in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _safe_delete_file, tmp_path)