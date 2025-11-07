"""
Vercel serverless function entry point
SIMPLIFIED VERSION - Minimal code, maximum reliability
"""
import sys
import os

# Write to stderr immediately
sys.stderr.write("API/INDEX.PY: STARTING\n")
sys.stderr.flush()

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.stderr.write(f"Path: {project_root}\n")
sys.stderr.flush()

# Import FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.stderr.write("FastAPI imported\n")
sys.stderr.flush()

# Create app
app = FastAPI(title="AI Resume Builder", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic endpoints
@app.get("/")
def root():
    return {"message": "AI Resume Builder is running 🚀", "status": "operational"}

@app.get("/health")
def health():
    return {"status": "healthy", "api": "running"}

# Try to add router (non-blocking)
try:
    from app.api.routes_resume import router
    app.include_router(router, prefix="/api/v1/resumes", tags=["resumes"])
    sys.stderr.write("Router added\n")
except Exception as e:
    sys.stderr.write(f"Router not added: {e}\n")
    @app.get("/api/v1/resumes/status")
    def router_status():
        return {"status": "Router not available", "error": str(e)}

sys.stderr.write("App ready\n")
sys.stderr.flush()

# Export handler for Vercel
handler = app
