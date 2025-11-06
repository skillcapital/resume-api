import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import router safely - if it fails, we'll create a minimal app
try:
    from app.api.routes_resume import router as resume_router
    ROUTER_AVAILABLE = True
except Exception as e:
    # If router import fails, create a dummy router
    from fastapi import APIRouter
    resume_router = APIRouter()
    ROUTER_AVAILABLE = False
    import sys
    print(f"Warning: Failed to import resume router: {str(e)}", file=sys.stderr)

# Import config safely
try:
    from app.core.config import FRONTEND_URL
except Exception:
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app = FastAPI(
    title="AI Resume Builder",
    description="Build and improve resumes with AI assistance",
    version="1.0.0"
)

# Configure CORS - flexible for backend-only or with frontend
# If FRONTEND_URL is set, use specific origins; otherwise allow all origins
if FRONTEND_URL and FRONTEND_URL != "http://localhost:3000":
    # Specific frontend URL provided - use restrictive CORS
    allowed_origins = [
        FRONTEND_URL,
        "https://supabase-skillcapital-lms-git-2c784d-tech-kdigitalais-projects.vercel.app",  # Preview frontend URL
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Alternative localhost
    ]
    # Remove duplicates while preserving order
    allowed_origins = list(dict.fromkeys(allowed_origins))
    allow_credentials = True
else:
    # No specific frontend URL - allow all origins (backend-only deployment)
    allowed_origins = ["*"]
    allow_credentials = False  # Cannot use credentials with wildcard origin

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Only include router if it was successfully imported
if ROUTER_AVAILABLE:
    app.include_router(resume_router, prefix="/api/v1/resumes", tags=["resumes"])
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
    return {"status": "healthy"}

