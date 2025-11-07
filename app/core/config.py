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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Supabase client - lazy initialization to reduce cold start time
# Don't create client at import time, only when needed
supabase: Optional[Client] = None
_supabase_initialized = False

def get_supabase_client():
    """
    Lazy initialization of Supabase client.
    Only creates client when first accessed, not at import time.
    This reduces cold start time on Vercel.
    """
    global supabase, _supabase_initialized
    
    # Return existing client if already initialized
    if _supabase_initialized:
        return supabase
    
    # Initialize only if available and credentials are set
    if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            _supabase_initialized = True
            return supabase
        except Exception as e:
            # Log error but don't crash
            import sys
            print(f"Warning: Failed to initialize Supabase client: {str(e)}", file=sys.stderr)
            _supabase_initialized = True  # Mark as attempted to avoid retries
            supabase = None
            return None
    
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

