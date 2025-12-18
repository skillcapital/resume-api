import os
from typing import Optional

# Try to load environment variables, but don't fail if dotenv is not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If dotenv fails, continue without it (environment variables may be set elsewhere)
    pass

# Try to import Supabase, but don't fail if it's not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Validate Supabase URL format
def validate_supabase_url(url: str):
    """
    Validate Supabase URL format.
    Returns (is_valid, error_message)
    """
    if not url:
        return False, "SUPABASE_URL is not set in environment variables"
    
    # Check if it starts with http:// or https://
    if not url.startswith(("http://", "https://")):
        return False, f"SUPABASE_URL must start with http:// or https://. Got: {url[:20]}..."
    
    # Check if it contains .supabase.co
    if ".supabase.co" not in url:
        return False, f"SUPABASE_URL should contain '.supabase.co'. Got: {url[:50]}..."
    
    # Check for common issues
    if " " in url:
        return False, "SUPABASE_URL contains spaces. Remove any spaces."
    
    return True, ""

# Supabase client - lazy initialization to reduce cold start time
# Don't create client at import time, only when needed
supabase: Optional[Client] = None
_supabase_initialized = False

def get_supabase_client(force_new: bool = False):
    """
    Lazy initialization of Supabase client.
    Only creates client when first accessed, not at import time.
    This reduces cold start time on Vercel.
    
    Args:
        force_new: If True, create a new client even if one exists (useful for retries)
    """
    global supabase, _supabase_initialized
    
    # Return existing client if already initialized and not forcing new
    if _supabase_initialized and supabase is not None and not force_new:
        return supabase
    
    # Validate URL format first
    if SUPABASE_URL:
        is_valid, error_msg = validate_supabase_url(SUPABASE_URL)
        if not is_valid:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid Supabase URL: {error_msg}")
            if not force_new:
                _supabase_initialized = True
            return None
    
    # Initialize only if available and credentials are set
    if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
        try:
            # Create new client (will overwrite existing if force_new=True)
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            _supabase_initialized = True
            return supabase
        except Exception as e:
            # Log error with more details
            import sys
            import logging
            logger = logging.getLogger(__name__)
            error_str = str(e).lower()
            
            # Provide specific error messages for common issues
            if "getaddrinfo" in error_str or "errno 11001" in error_str or "dns" in error_str:
                error_detail = f"DNS resolution failed. Cannot resolve Supabase URL: {SUPABASE_URL[:50]}... Check your SUPABASE_URL in .env file. Error: {str(e)}"
            elif "connection" in error_str or "network" in error_str:
                error_detail = f"Network connection failed. Check your internet connection and Supabase URL. Error: {str(e)}"
            else:
                error_detail = f"Failed to initialize Supabase client: {str(e)}"
            
            logger.error(error_detail)
            print(f"ERROR: {error_detail}", file=sys.stderr)
            
            # Don't mark as initialized if it failed - allow retry
            if not force_new:
                _supabase_initialized = True
                supabase = None
            return None
    
    if not force_new:
        _supabase_initialized = True
    return None

# For backward compatibility - initialize on first access
# This allows existing code to work without changes
def _init_supabase_if_needed():
    """Initialize Supabase if not already done."""
    if not _supabase_initialized:
        get_supabase_client()

# Frontend URL - can be different per branch/environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Bucket names
SUPABASE_BUCKET_UPLOADS = os.getenv("SUPABASE_BUCKET_UPLOADS", "uploads")
SUPABASE_BUCKET_EXPORTS = os.getenv("SUPABASE_BUCKET_EXPORTS", "exports")

