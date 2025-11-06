import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Frontend URL - can be different per branch/environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bucket names
SUPABASE_BUCKET_UPLOADS = os.getenv("SUPABASE_BUCKET_UPLOADS", "uploads")
SUPABASE_BUCKET_EXPORTS = os.getenv("SUPABASE_BUCKET_EXPORTS", "exports")

