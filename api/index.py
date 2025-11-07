"""
Vercel serverless function entry point
SIMPLIFIED VERSION - Minimal code, maximum reliability
"""
import sys
import os

# Write to stderr immediately
sys.stderr.write("API/INDEX.PY: STARTING\n")
sys.stderr.flush()

# Add project root to path (CRITICAL for Vercel)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Ensure both project root and current directory are in path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

sys.stderr.write(f"Project root: {project_root}\n")
sys.stderr.write(f"Current dir: {current_dir}\n")
sys.stderr.write(f"Python path: {sys.path[:3]}\n")  # Show first 3 entries
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

# Try to add router (non-blocking) - WITH DETAILED ERROR LOGGING
sys.stderr.write("Attempting to import router...\n")
sys.stderr.flush()

try:
    # Check if app directory exists
    app_dir = os.path.join(project_root, "app")
    routes_file = os.path.join(app_dir, "api", "routes_resume.py")
    
    sys.stderr.write(f"Checking routes file: {routes_file}\n")
    sys.stderr.write(f"File exists: {os.path.exists(routes_file)}\n")
    sys.stderr.write(f"App dir exists: {os.path.exists(app_dir)}\n")
    sys.stderr.flush()
    
    # Import router with detailed error capture
    from app.api.routes_resume import router
    sys.stderr.write("✅ Router module imported successfully\n")
    sys.stderr.flush()
    
    # Add router to app
    app.include_router(router, prefix="/api/v1/resumes", tags=["resumes"])
    sys.stderr.write("✅ Router added to app successfully\n")
    sys.stderr.flush()
    
except ImportError as e:
    import traceback
    sys.stderr.write(f"❌ Router import failed (ImportError):\n")
    sys.stderr.write(f"Error: {str(e)}\n")
    sys.stderr.write("Full traceback:\n")
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    
    @app.get("/api/v1/resumes/status")
    def router_status():
        return {
            "status": "Router not available",
            "error_type": "ImportError",
            "error": str(e),
            "note": "Check Vercel logs for full traceback"
        }
        
except Exception as e:
    import traceback
    sys.stderr.write(f"❌ Router import failed (Unexpected error):\n")
    sys.stderr.write(f"Error: {str(e)}\n")
    sys.stderr.write("Full traceback:\n")
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    
    @app.get("/api/v1/resumes/status")
    def router_status():
        return {
            "status": "Router not available",
            "error_type": type(e).__name__,
            "error": str(e),
            "note": "Check Vercel logs for full traceback"
        }

sys.stderr.write("App ready\n")
sys.stderr.flush()

# Export handler for Vercel
handler = app
