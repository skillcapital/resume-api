"""
Vercel serverless function entry point
PERMANENT FIX: Start with minimal app, then optionally enhance with full app
"""
import sys
import os

# CRITICAL: Write to stderr IMMEDIATELY - this must appear if Python runs
sys.stderr.write("=" * 80 + "\n")
sys.stderr.write("API/INDEX.PY: FILE LOADED - Python is running!\n")
sys.stderr.write(f"Python version: {sys.version}\n")
sys.stderr.write(f"Current dir: {os.getcwd()}\n")
sys.stderr.write(f"File location: {__file__}\n")
sys.stderr.write("=" * 80 + "\n")
sys.stderr.flush()

# Add project root to path
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    sys.stderr.write(f"Project root added to path: {project_root}\n")
    sys.stderr.flush()
except Exception as e:
    sys.stderr.write(f"Path setup error: {e}\n")
    sys.stderr.flush()

# STEP 1: Import FastAPI directly (no app.main import yet)
sys.stderr.write("Step 1: Importing FastAPI directly...\n")
sys.stderr.flush()

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    sys.stderr.write("✅ FastAPI imported successfully\n")
    sys.stderr.flush()
except Exception as e:
    sys.stderr.write(f"❌ CRITICAL: FastAPI import failed: {e}\n")
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    # If FastAPI can't be imported, we're completely broken
    def handler(request):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "FastAPI import failed", "message": "' + str(e).replace('"', '\\"') + '"}'
        }
    sys.stderr.write("Created fallback handler (FastAPI unavailable)\n")
    sys.stderr.flush()
else:
    # STEP 2: Create minimal working app FIRST
    sys.stderr.write("Step 2: Creating minimal FastAPI app...\n")
    sys.stderr.flush()
    
    app = FastAPI(
        title="AI Resume Builder",
        description="Build and improve resumes with AI assistance",
        version="1.0.0"
    )
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Basic endpoints that work without any imports
    @app.get("/")
    def root():
        return {"message": "AI Resume Builder is running 🚀", "status": "operational"}
    
    @app.get("/health")
    def health():
        return {"status": "healthy", "api": "running"}
    
    sys.stderr.write("✅ Minimal app created with basic endpoints\n")
    sys.stderr.flush()
    
    # STEP 3: Try to import and add router (optional enhancement)
    sys.stderr.write("Step 3: Attempting to import router (optional)...\n")
    sys.stderr.flush()
    
    try:
        from app.api.routes_resume import router as resume_router
        app.include_router(resume_router, prefix="/api/v1/resumes", tags=["resumes"])
        sys.stderr.write("✅ Router imported and added successfully\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"⚠️ Router import failed (non-critical): {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        # Add a status endpoint to indicate router is unavailable
        @app.get("/api/v1/resumes/status")
        def router_status():
            return {"status": "Router not available", "error": str(e)}
    
    # STEP 4: Enhance health endpoint with Supabase check (optional)
    sys.stderr.write("Step 4: Enhancing health endpoint...\n")
    sys.stderr.flush()
    
    try:
        from app.core.config import get_supabase_client, SUPABASE_URL, SUPABASE_KEY
        
        # Replace the simple health endpoint with enhanced one
        @app.get("/health")
        def health_check():
            """Health check endpoint with Supabase status"""
            health = {
                "status": "healthy",
                "api": "running",
                "supabase": {
                    "configured": bool(SUPABASE_URL and SUPABASE_KEY),
                    "connected": False
                }
            }
            
            if health["supabase"]["configured"]:
                try:
                    supabase = get_supabase_client()
                    if supabase is None:
                        health["status"] = "degraded"
                        health["supabase"]["error"] = "Client not initialized"
                    else:
                        try:
                            supabase.table("resumes").select("id").limit(0).execute()
                            health["supabase"]["connected"] = True
                        except Exception as e:
                            health["status"] = "degraded"
                            health["supabase"]["connected"] = False
                            health["supabase"]["error"] = str(e)
                except Exception as e:
                    health["status"] = "degraded"
                    health["supabase"]["connected"] = False
                    health["supabase"]["error"] = f"Failed to get client: {str(e)}"
            else:
                health["status"] = "degraded"
                health["supabase"]["error"] = "Not configured (missing SUPABASE_URL or SUPABASE_SERVICE_KEY)"
            
            status_code = 200 if health["status"] == "healthy" else 503
            return JSONResponse(status_code=status_code, content=health)
        
        sys.stderr.write("✅ Health endpoint enhanced with Supabase check\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"⚠️ Health endpoint enhancement failed (non-critical): {e}\n")
        sys.stderr.flush()
        # Keep the simple health endpoint
    
    # Set handler
    handler = app
    sys.stderr.write("✅ Handler set to app\n")
    sys.stderr.flush()

# Final export
sys.stderr.write("=" * 80 + "\n")
sys.stderr.write(f"✅ Handler ready: {type(handler).__name__}\n")
sys.stderr.write("=" * 80 + "\n")
sys.stderr.flush()

# Export for Vercel
# Vercel Python runtime expects 'handler' or 'app' variable
