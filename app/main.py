import sys
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Diagnostic: Catch fatal import errors
try:
    # Import router safely - if it fails, we'll create a minimal app
    try:
        from app.api.routes_resume import router as resume_router
        ROUTER_AVAILABLE = True
        print("✅ Router imported successfully", file=sys.stderr)
    except Exception as e:
        print("❌ Router import failed:", str(e), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        from fastapi import APIRouter
        resume_router = APIRouter()
        ROUTER_AVAILABLE = False
        print("⚠️ Using fallback router", file=sys.stderr)

    app = FastAPI(
        title="AI Resume Builder",
        description="Build and improve resumes with AI assistance",
        version="1.0.0"
    )

    # Configure CORS - allow all origins for backend-only deployment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Cannot use credentials with wildcard origin
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Only include router if it was successfully imported
    if ROUTER_AVAILABLE:
        app.include_router(resume_router, prefix="/api/v1/resumes", tags=["resumes"])
        print("✅ Router included in app", file=sys.stderr)
    else:
        # Add a fallback route to indicate router is not available
        @app.get("/api/v1/resumes/status")
        def router_status():
            return {"status": "Router not available", "error": "Failed to import resume router"}

    @app.get("/")
    def root():
        return {"message": "AI Resume Builder is running 🚀", "docs": "/docs"}

    @app.get("/health")
    def health_check():
        """
        Health check endpoint that verifies API and Supabase connection
        """
        # Import here to avoid circular imports and handle errors gracefully
        try:
            from app.core.config import get_supabase_client, SUPABASE_URL, SUPABASE_KEY
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "degraded",
                    "api": "running",
                    "supabase": {
                        "configured": False,
                        "connected": False,
                        "error": f"Failed to import config: {str(e)}"
                    }
                }
            )
        
        health = {
            "status": "healthy",
            "api": "running",
            "supabase": {
                "configured": bool(SUPABASE_URL and SUPABASE_KEY),
                "connected": False
            }
        }
        
        # Check Supabase connection (lazy initialization)
        if health["supabase"]["configured"]:
            try:
                supabase = get_supabase_client()
                if supabase is None:
                    health["status"] = "degraded"
                    health["supabase"]["error"] = "Client not initialized"
                else:
                    try:
                        # Simple connection test - query with limit 0 (fastest check)
                        # This verifies the connection without fetching actual data
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

    print("✅ FastAPI app initialized successfully", file=sys.stderr)

except Exception as e:
    print("❌ Fatal import error:", str(e), file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    # Create minimal error app so Vercel doesn't crash completely
    app = FastAPI(title="Error Handler")
    @app.get("/{full_path:path}")
    @app.get("/")
    async def error_handler(full_path: str = "/"):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application initialization failed",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        )

# Export for Vercel (required for serverless deployment)
# Vercel Python runtime looks for 'handler' or 'app'
handler = app
print("✅ Handler exported for Vercel", file=sys.stderr)