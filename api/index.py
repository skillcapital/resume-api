"""
Vercel serverless function entry point
ULTRA-SAFE VERSION: No imports from app.main, builds everything from scratch
"""
import sys
import os

# CRITICAL: Write to stderr IMMEDIATELY - this must appear if Python runs
try:
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.write("API/INDEX.PY: FILE LOADED - Python is running!\n")
    sys.stderr.write(f"Python version: {sys.version}\n")
    sys.stderr.write(f"Current dir: {os.getcwd()}\n")
    sys.stderr.write(f"File location: {__file__}\n")
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.flush()
except:
    pass

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

# STEP 1: Import FastAPI directly (MUST work)
sys.stderr.write("Step 1: Importing FastAPI...\n")
sys.stderr.flush()

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    sys.stderr.write("✅ FastAPI imported successfully\n")
    sys.stderr.flush()
    FASTAPI_AVAILABLE = True
except Exception as e:
    sys.stderr.write(f"❌ CRITICAL: FastAPI import failed: {e}\n")
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    FASTAPI_AVAILABLE = False
    handler = None
    app = None

if FASTAPI_AVAILABLE:
    # STEP 2: Create minimal working app FIRST
    sys.stderr.write("Step 2: Creating FastAPI app...\n")
    sys.stderr.flush()
    
    try:
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
        
        # STEP 3: Try to import router (WITH EXTREME CAUTION)
        sys.stderr.write("Step 3: Attempting to import router (optional)...\n")
        sys.stderr.flush()
        
        router_imported = False
        try:
            # Import router module first to check if it exists
            import importlib.util
            router_path = os.path.join(project_root, "app", "api", "routes_resume.py")
            
            if os.path.exists(router_path):
                sys.stderr.write(f"Router file exists: {router_path}\n")
                sys.stderr.flush()
                
                # Try importing with importlib to get better error messages
                spec = importlib.util.spec_from_file_location("routes_resume", router_path)
                if spec and spec.loader:
                    # Import the module
                    routes_module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(routes_module)
                        if hasattr(routes_module, 'router'):
                            app.include_router(routes_module.router, prefix="/api/v1/resumes", tags=["resumes"])
                            router_imported = True
                            sys.stderr.write("✅ Router imported and added successfully\n")
                            sys.stderr.flush()
                        else:
                            sys.stderr.write("⚠️ Router module loaded but no 'router' attribute found\n")
                            sys.stderr.flush()
                    except Exception as import_err:
                        sys.stderr.write(f"⚠️ Error executing router module: {import_err}\n")
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                        sys.stderr.flush()
                else:
                    sys.stderr.write("⚠️ Could not create spec for router module\n")
                    sys.stderr.flush()
            else:
                sys.stderr.write(f"⚠️ Router file not found: {router_path}\n")
                sys.stderr.flush()
                
        except Exception as e:
            sys.stderr.write(f"⚠️ Router import failed (non-critical): {e}\n")
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
        
        if not router_imported:
            # Add a status endpoint to indicate router is unavailable
            @app.get("/api/v1/resumes/status")
            def router_status():
                return {"status": "Router not available", "note": "Router import failed or not found"}
        
        # STEP 4: Enhance health endpoint (optional)
        sys.stderr.write("Step 4: Enhancing health endpoint (optional)...\n")
        sys.stderr.flush()
        
        try:
            # Try to import config module safely
            config_path = os.path.join(project_root, "app", "core", "config.py")
            if os.path.exists(config_path):
                spec = importlib.util.spec_from_file_location("config", config_path)
                if spec and spec.loader:
                    config_module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(config_module)
                        
                        # Replace health endpoint with enhanced version
                        @app.get("/health")
                        def health_check():
                            """Health check endpoint with Supabase status"""
                            try:
                                get_supabase_client = getattr(config_module, 'get_supabase_client', None)
                                SUPABASE_URL = getattr(config_module, 'SUPABASE_URL', None)
                                SUPABASE_KEY = getattr(config_module, 'SUPABASE_KEY', None)
                                
                                health = {
                                    "status": "healthy",
                                    "api": "running",
                                    "supabase": {
                                        "configured": bool(SUPABASE_URL and SUPABASE_KEY),
                                        "connected": False
                                    }
                                }
                                
                                if health["supabase"]["configured"] and get_supabase_client:
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
                                    health["supabase"]["error"] = "Not configured"
                                
                                status_code = 200 if health["status"] == "healthy" else 503
                                return JSONResponse(status_code=status_code, content=health)
                            except Exception as e:
                                return JSONResponse(
                                    status_code=503,
                                    content={
                                        "status": "degraded",
                                        "api": "running",
                                        "supabase": {"error": str(e)}
                                    }
                                )
                        
                        sys.stderr.write("✅ Health endpoint enhanced\n")
                        sys.stderr.flush()
                    except Exception as e:
                        sys.stderr.write(f"⚠️ Config module execution failed: {e}\n")
                        sys.stderr.flush()
        except Exception as e:
            sys.stderr.write(f"⚠️ Health enhancement failed (non-critical): {e}\n")
            sys.stderr.flush()
        
        # Set handler
        handler = app
        sys.stderr.write("✅ Handler set to app\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"❌ App creation failed: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        handler = None
        app = None

# CRITICAL: Ensure handler is ALWAYS defined
if handler is None:
    sys.stderr.write("⚠️ Handler is None, creating fallback\n")
    sys.stderr.flush()
    
    if app is not None:
        handler = app
    else:
        # Last resort: Create a basic function handler
        def fallback_handler(request):
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Handler initialization failed", "status": "error"}'
            }
        handler = fallback_handler

# Final export
sys.stderr.write("=" * 80 + "\n")
sys.stderr.write(f"✅ Handler ready: {type(handler).__name__}\n")
sys.stderr.write("=" * 80 + "\n")
sys.stderr.flush()

# Export for Vercel - CRITICAL
# Vercel Python runtime expects 'handler' or 'app' variable at module level
