"""
Vercel serverless function entry point
ULTRA-DEFENSIVE VERSION - Prevents ALL crashes, always returns a handler
"""
import sys
import os

# CRITICAL: Ensure handler is ALWAYS defined, even if everything fails
handler = None
app = None

# Write to stderr immediately - this MUST work
try:
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.write("API/INDEX.PY: STARTING\n")
    sys.stderr.write(f"Python: {sys.version}\n")
    sys.stderr.write(f"File: {__file__}\n")
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.flush()
except:
    pass  # If even stderr fails, continue anyway

# Add project root to path (CRITICAL for Vercel)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    sys.stderr.write(f"Project root: {project_root}\n")
    sys.stderr.write(f"Current dir: {current_dir}\n")
    sys.stderr.flush()
except Exception as e:
    sys.stderr.write(f"Path setup error: {e}\n")
    sys.stderr.flush()

# STEP 1: Import FastAPI (MUST work or we're done)
try:
    sys.stderr.write("Step 1: Importing FastAPI...\n")
    sys.stderr.flush()
    
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    sys.stderr.write("✅ FastAPI imported\n")
    sys.stderr.flush()
    FASTAPI_AVAILABLE = True
except Exception as e:
    sys.stderr.write(f"❌ CRITICAL: FastAPI import failed: {e}\n")
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    FASTAPI_AVAILABLE = False

# STEP 2: Create minimal app (MUST work)
if FASTAPI_AVAILABLE:
    try:
        sys.stderr.write("Step 2: Creating FastAPI app...\n")
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
        
        # Basic endpoints that ALWAYS work
        @app.get("/")
        def root():
            return {
                "message": "AI Resume Builder is running 🚀",
                "status": "operational",
                "router": "checking..."
            }
        
        @app.get("/health")
        def health():
            return {"status": "healthy", "api": "running"}
        
        sys.stderr.write("✅ Minimal app created\n")
        sys.stderr.flush()
        
    except Exception as e:
        sys.stderr.write(f"❌ App creation failed: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        app = None

# STEP 3: Try to import router (OPTIONAL - non-blocking)
if app is not None:
    try:
        sys.stderr.write("Step 3: Attempting to import router...\n")
        sys.stderr.flush()
        
        # Use importlib for safer imports
        import importlib.util
        
        # Check file exists first
        app_dir = os.path.join(project_root, "app")
        routes_file = os.path.join(app_dir, "api", "routes_resume.py")
        
        sys.stderr.write(f"Routes file: {routes_file}\n")
        sys.stderr.write(f"Exists: {os.path.exists(routes_file)}\n")
        sys.stderr.flush()
        
        if os.path.exists(routes_file):
            # Try direct import first (faster)
            try:
                from app.api.routes_resume import router
                sys.stderr.write("✅ Router imported (direct)\n")
                sys.stderr.flush()
                
                app.include_router(router, prefix="/api/v1/resumes", tags=["resumes"])
                sys.stderr.write("✅ Router added to app\n")
                sys.stderr.flush()
                
            except Exception as direct_error:
                sys.stderr.write(f"Direct import failed: {direct_error}\n")
                sys.stderr.flush()
                
                # Fallback: Try importlib (more defensive)
                try:
                    spec = importlib.util.spec_from_file_location(
                        "routes_resume",
                        routes_file
                    )
                    if spec and spec.loader:
                        routes_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(routes_module)
                        
                        if hasattr(routes_module, 'router'):
                            app.include_router(
                                routes_module.router,
                                prefix="/api/v1/resumes",
                                tags=["resumes"]
                            )
                            sys.stderr.write("✅ Router added (importlib)\n")
                            sys.stderr.flush()
                        else:
                            sys.stderr.write("⚠️ Module loaded but no 'router' attribute\n")
                            sys.stderr.flush()
                except Exception as importlib_error:
                    sys.stderr.write(f"Importlib also failed: {importlib_error}\n")
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.flush()
        else:
            sys.stderr.write(f"⚠️ Routes file not found: {routes_file}\n")
            sys.stderr.flush()
            
    except Exception as e:
        sys.stderr.write(f"⚠️ Router import attempt failed: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
    
    # Add status endpoint regardless of router success
    @app.get("/api/v1/resumes/status")
    def router_status():
        return {
            "status": "Router status unknown",
            "note": "Check Vercel logs for import details"
        }

# STEP 4: Ensure handler is ALWAYS defined
if app is not None:
    handler = app
    sys.stderr.write("✅ Handler = app\n")
else:
    # LAST RESORT: Create a minimal function handler
    sys.stderr.write("⚠️ Creating fallback handler\n")
    sys.stderr.flush()
    
    def fallback_handler(request):
        """Fallback handler if app creation fails"""
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Handler initialization failed", "status": "error", "message": "Check Vercel logs"}'
        }
    handler = fallback_handler

# Final confirmation
try:
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.write(f"✅ FINAL: Handler type = {type(handler).__name__}\n")
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.flush()
except:
    pass

# CRITICAL: Export handler for Vercel
# This MUST exist at module level