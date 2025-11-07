from app.core.config import get_supabase_client, SUPABASE_BUCKET_EXPORTS
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

def _get_supabase():
    """Get Supabase client with lazy initialization."""
    return get_supabase_client()

def save_resume_raw(text: str) -> str:
    """
    Save raw resume text to database.
    """
    supabase = _get_supabase()
    if not supabase:
        raise Exception("Supabase client not initialized. Check your .env file.")
    
    resume_id = str(uuid.uuid4())
    
    try:
        result = supabase.table("resumes").insert({
            "id": resume_id,
            "raw_text": text,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        return resume_id
    except Exception as e:
        raise Exception(f"Error saving resume: {str(e)}")

def save_resume_version(resume_id: str, content: Dict[str, Any], version_type: str = "improved") -> None:
    """
    Save a resume version (improved or tailored) to database.
    """
    supabase = _get_supabase()
    if not supabase:
        raise Exception("Supabase client not initialized. Check your .env file.")
    
    try:
        supabase.table("resume_versions").insert({
            "resume_id": resume_id,
            "content": content,
            "version_type": version_type,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        raise Exception(f"Error saving resume version: {str(e)}")

def get_resume(resume_id: str) -> Optional[Dict[str, Any]]:
    """
    Get resume by ID.
    """
    supabase = _get_supabase()
    if not supabase:
        raise Exception("Supabase client not initialized. Check your .env file.")
    
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

def upload_pdf(resume_id: str, pdf_bytes: bytes, template: str = "default") -> str:
    """
    Upload PDF to Supabase storage and return public URL.
    Handles duplicate files by deleting existing file first.
    """
    supabase = _get_supabase()
    if not supabase:
        raise Exception("Supabase client not initialized. Check your .env file.")
    
    try:
        # Store each export under its resume folder and template file name
        # Example: <resume_id>/default.pdf, <resume_id>/modern.pdf
        safe_template = (template or "default").strip().lower()
        file_path = f"{resume_id}/{safe_template}.pdf"
        
        storage_bucket = supabase.storage.from_(SUPABASE_BUCKET_EXPORTS)
        
        # Try to delete existing file first to avoid 409 Duplicate error
        # Ignore errors if file doesn't exist
        try:
            storage_bucket.remove([file_path])
        except Exception:
            # File doesn't exist, which is fine - we'll create it
            pass
        
        # Upload the new file
        result = storage_bucket.upload(
            file_path,
            pdf_bytes,
            {"content-type": "application/pdf"}
        )
        
        # Get public URL
        public_url = storage_bucket.get_public_url(file_path)
        
        return public_url
    except Exception as e:
        raise Exception(f"Error uploading PDF: {str(e)}")

