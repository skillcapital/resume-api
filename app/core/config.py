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

# Supabase client - initialize safely to prevent import errors
supabase: Optional[Client] = None
if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        # Log error but don't crash - supabase will be None
        # This allows the app to start even if Supabase config is invalid
        import sys
        print(f"Warning: Failed to initialize Supabase client: {str(e)}", file=sys.stderr)
        supabase = None

# Bucket names
SUPABASE_BUCKET_UPLOADS = os.getenv("SUPABASE_BUCKET_UPLOADS", "uploads")
SUPABASE_BUCKET_EXPORTS = os.getenv("SUPABASE_BUCKET_EXPORTS", "exports")

