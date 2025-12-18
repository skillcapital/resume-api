from app.core.config import get_supabase_client, SUPABASE_BUCKET_EXPORTS
import random
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime

def _get_supabase(force_new: bool = False):
    """Get Supabase client with lazy initialization.
    
    Args:
        force_new: If True, create a new client even if one exists (useful for retries)
    """
    return get_supabase_client(force_new=force_new)

def save_resume_raw(text: str, max_retries: int = 5) -> str:
    """
    Save raw resume text to database.
    Uses retry logic with connection recreation to handle transient connection/resource errors.
    
    Args:
        text: Raw resume text to save
        max_retries: Maximum number of retry attempts (increased to 5 for better reliability)
    """
    resume_id = str(uuid.uuid4())
    
    last_exception = None
    for attempt in range(max_retries):
        try:
            # Get fresh Supabase client on each retry to avoid stale connections
            supabase = get_supabase_client(force_new=(attempt > 0))
            if not supabase:
                raise Exception("Supabase client not initialized. Check your .env file.")
            
            result = supabase.table("resumes").insert({
                "id": resume_id,
                "raw_text": text,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            return resume_id
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Expanded list of retryable errors (including DNS/network errors)
            retryable_keywords = [
                "busy", "locked", "resource", "errno 16", "errno 11", 
                "connection", "timeout", "temporary", "network", 
                "socket", "broken pipe", "connection reset", 
                "too many connections", "connection pool", "429",  # Rate limit
                "503", "502", "504",  # Server errors
                "getaddrinfo", "dns", "name resolution", "errno 11001",  # DNS errors
                "connecterror", "network unreachable"  # Network errors
            ]
            
            # Check if it's a retryable error
            is_retryable = any(keyword in error_msg for keyword in retryable_keywords)
            
            if is_retryable:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter: 0.2s, 0.4s, 0.8s, 1.6s, 3.2s
                    base_wait = 0.2 * (2 ** attempt)
                    # Add small random jitter to avoid thundering herd
                    jitter = random.uniform(0, 0.1 * (attempt + 1))
                    wait_time = base_wait + jitter
                    time.sleep(wait_time)
                    continue
                else:
                    # Last attempt failed
                    raise Exception(f"Error saving resume: Resource busy or connection issue after {max_retries} attempts. {str(e)}")
            else:
                # Non-retryable error (e.g., validation error), raise immediately
                raise Exception(f"Error saving resume: {str(e)}")
    
    # If we get here, all retries failed
    raise Exception(f"Error saving resume after {max_retries} attempts: {str(last_exception)}")

def save_resume_version(resume_id: str, content: Dict[str, Any], version_type: str = "improved", max_retries: int = 5) -> None:
    """
    Save a resume version (improved or tailored) to database.
    Uses retry logic with connection recreation to handle transient connection/resource errors.
    
    Args:
        resume_id: UUID of the resume
        content: Resume version content dictionary
        version_type: Type of version (improved, tailored, etc.)
        max_retries: Maximum number of retry attempts (increased to 5 for better reliability)
    """
    # Validate UUID format
    try:
        uuid.UUID(resume_id)
    except (ValueError, TypeError):
        raise Exception(f"Invalid resume ID format: '{resume_id}'. Resume ID must be a valid UUID.")
    
    # Check if resume exists before saving version (only on first attempt to avoid repeated checks)
    resume = get_resume(resume_id)
    if not resume:
        raise Exception(f"Resume not found. Resume ID '{resume_id}' does not exist in the database. Please create the resume first using /api/v1/resumes/create or /api/v1/resumes/upload.")
    
    last_exception = None
    for attempt in range(max_retries):
        try:
            # Get fresh Supabase client on each retry to avoid stale connections
            supabase = get_supabase_client(force_new=(attempt > 0))
            if not supabase:
                raise Exception("Supabase client not initialized. Check your .env file.")
            
            supabase.table("resume_versions").insert({
                "resume_id": resume_id,
                "content": content,
                "version_type": version_type,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return  # Success
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Check for foreign key constraint violation (non-retryable)
            if "foreign key constraint" in error_msg or "23503" in error_msg:
                raise Exception(f"Resume not found. Resume ID '{resume_id}' does not exist in the database. Please create the resume first using /api/v1/resumes/create or /api/v1/resumes/upload.")
            
            # Expanded list of retryable errors (including DNS/network errors)
            retryable_keywords = [
                "busy", "locked", "resource", "errno 16", "errno 11", 
                "connection", "timeout", "temporary", "network", 
                "socket", "broken pipe", "connection reset", 
                "too many connections", "connection pool", "429",  # Rate limit
                "503", "502", "504",  # Server errors
                "getaddrinfo", "dns", "name resolution", "errno 11001",  # DNS errors
                "connecterror", "network unreachable"  # Network errors
            ]
            
            # Check if it's a retryable error
            is_retryable = any(keyword in error_msg for keyword in retryable_keywords)
            
            if is_retryable:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter: 0.2s, 0.4s, 0.8s, 1.6s, 3.2s
                    base_wait = 0.2 * (2 ** attempt)
                    # Add small random jitter to avoid thundering herd
                    jitter = random.uniform(0, 0.1 * (attempt + 1))
                    wait_time = base_wait + jitter
                    time.sleep(wait_time)
                    continue
                else:
                    # Last attempt failed
                    raise Exception(f"Error saving resume version: Resource busy or connection issue after {max_retries} attempts. {str(e)}")
            else:
                # Non-retryable error, raise immediately
                raise Exception(f"Error saving resume version: {str(e)}")
    
    # If we get here, all retries failed
    raise Exception(f"Error saving resume version after {max_retries} attempts: {str(last_exception)}")

def get_resume(resume_id: str) -> Optional[Dict[str, Any]]:
    """
    Get resume by ID.
    """
    supabase = _get_supabase()
    if not supabase:
        raise Exception("Supabase client not initialized. Check your .env file.")
    
    # Validate UUID format before querying database
    try:
        uuid.UUID(resume_id)
    except (ValueError, TypeError):
        raise Exception(f"Invalid resume ID format: '{resume_id}'. Resume ID must be a valid UUID.")
    
    try:
        result = supabase.table("resumes").select("*").eq("id", resume_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        raise Exception(f"Error fetching resume: {str(e)}")

def get_latest_resume_version(resume_id: str, version_type: str = "latest") -> Optional[Dict[str, Any]]:
    """
    Get latest resume version.
    """
    supabase = _get_supabase()
    if not supabase:
        raise Exception("Supabase client not initialized. Check your .env file.")
    
    # Validate UUID format before querying database
    try:
        uuid.UUID(resume_id)
    except (ValueError, TypeError):
        raise Exception(f"Invalid resume ID format: '{resume_id}'. Resume ID must be a valid UUID.")
    
    try:
        query = supabase.table("resume_versions").select("*").eq("resume_id", resume_id)
        
        if version_type != "latest":
            query = query.eq("version_type", version_type)
        
        result = query.order("created_at", desc=True).limit(1).execute()
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        raise Exception(f"Error fetching resume version: {str(e)}")

def upload_pdf(resume_id: str, pdf_bytes: bytes, template: str = "default", max_retries: int = 3) -> str:
    """
    Upload PDF to Supabase storage and return public URL.
    Handles duplicate files by deleting existing file first.
    Uses retry logic to handle file lock/resource busy errors.
    
    Args:
        resume_id: UUID of the resume
        pdf_bytes: PDF file content as bytes
        template: Template name (default, modern, etc.)
        max_retries: Maximum number of retry attempts for upload
    """
    supabase = _get_supabase()
    if not supabase:
        raise Exception("Supabase client not initialized. Check your .env file.")
    
    # Store each export under its resume folder and template file name
    # Example: <resume_id>/default.pdf, <resume_id>/modern.pdf
    safe_template = (template or "default").strip().lower()
    file_path = f"{resume_id}/{safe_template}.pdf"
    
    storage_bucket = supabase.storage.from_(SUPABASE_BUCKET_EXPORTS)
    
    # Try to delete existing file first to avoid 409 Duplicate error
    # Ignore errors if file doesn't exist
    try:
        storage_bucket.remove([file_path])
        # Small delay to ensure deletion is complete before upload
        time.sleep(0.1)
    except Exception:
        # File doesn't exist, which is fine - we'll create it
        pass
    
    # Retry upload with exponential backoff to handle resource busy errors
    last_exception = None
    for attempt in range(max_retries):
        try:
            # First, try to update (overwrite) existing file
            # This avoids the need to delete first
            try:
                result = storage_bucket.update(
                    file_path,
                    pdf_bytes,
                    file_options={"content-type": "application/pdf"}
                )
            except Exception as update_error:
                # If update fails (file doesn't exist), try upload
                error_msg = str(update_error).lower()
                if "not found" in error_msg or "404" in error_msg or "does not exist" in error_msg:
                    # File doesn't exist, use upload instead
                    result = storage_bucket.upload(
                        file_path,
                        pdf_bytes,
                        file_options={"content-type": "application/pdf", "x-upsert": "true"}
                    )
                else:
                    # Re-raise if it's a different error
                    raise
            
            # Get public URL
            public_url = storage_bucket.get_public_url(file_path)
            
            return public_url
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Check if it's a resource busy or file lock error
            if any(keyword in error_msg for keyword in ["busy", "locked", "resource", "errno 16", "permission", "409", "conflict"]):
                if attempt < max_retries - 1:
                    # Try deleting the file again before retry
                    try:
                        storage_bucket.remove([file_path])
                        time.sleep(0.2 * (attempt + 1))  # Wait longer on each retry
                    except Exception:
                        pass  # Ignore deletion errors
                    
                    # Wait with exponential backoff before retrying
                    wait_time = 0.2 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    # Last attempt failed
                    raise Exception(f"Error uploading PDF: File is locked or resource is busy after {max_retries} attempts. {str(e)}")
            else:
                # Non-retryable error, raise immediately
                raise Exception(f"Error uploading PDF: {str(e)}")
    
    # If we get here, all retries failed
    raise Exception(f"Error uploading PDF after {max_retries} attempts: {str(last_exception)}")

