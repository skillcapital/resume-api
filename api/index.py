"""
Vercel serverless function entry point
Uses Vercel's standard api/ folder convention
This wrapper imports from app.main to ensure proper module resolution
"""
# CRITICAL: Import standard library first - these should NEVER fail
import sys
import os

# Immediate diagnostic output - this should ALWAYS appear if Python runs
# Use try/except to ensure we can log even if something fails
try:
    sys.stderr.write("=" * 60 + "\n")
    sys.stderr.write("API/INDEX.PY: Starting Vercel handler\n")
    sys.stderr.flush()
except:
    pass  # If even stderr fails, we're in deep trouble

try:
    import traceback
except:
    traceback = None

# Add project root to path to ensure imports work
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    sys.stderr.write(f"Current dir: {current_dir}\n")
    sys.stderr.write(f"Project root: {project_root}\n")
    sys.stderr.write(f"Python path (first 3): {sys.path[:3]}\n")
    sys.stderr.write("=" * 60 + "\n")
    sys.stderr.flush()
except Exception as e:
    sys.stderr.write(f"Error setting up paths: {str(e)}\n")
    sys.stderr.flush()
    current_dir = os.getcwd()
    project_root = current_dir

handler = None
app = None

try:
    sys.stderr.write("Attempting to import from app.main...\n")
    sys.stderr.flush()
    
    # Import app and handler from app.main
    from app.main import app, handler
    
    # Ensure handler exists
    if handler is None:
        handler = app
    
    sys.stderr.write(f"✅ Successfully imported from app.main\n")
    sys.stderr.write(f"Handler type: {type(handler).__name__}\n")
    sys.stderr.write(f"App type: {type(app).__name__ if app else 'None'}\n")
    sys.stderr.flush()
    
except Exception as e:
    sys.stderr.write(f"❌ Import from app.main failed: {str(e)}\n")
    if traceback:
        traceback.print_exc(file=sys.stderr)
    else:
        sys.stderr.write(f"Traceback unavailable\n")
    sys.stderr.flush()
    
    # Fallback: Create minimal error handler
    try:
        sys.stderr.write("Creating fallback error handler...\n")
        sys.stderr.flush()
        
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI(title="Error Handler")
        
        @app.get("/{full_path:path}")
        @app.get("/")
        async def error_handler(full_path: str = "/"):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Application import failed",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                    "path": full_path
                }
            )
        
        handler = app
        sys.stderr.write("✅ Fallback error handler created\n")
        sys.stderr.flush()
        
    except Exception as e2:
        sys.stderr.write(f"❌ Even fallback handler failed: {str(e2)}\n")
        if traceback:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        
        # Last resort: Basic function handler
        def basic_handler(request):
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Critical initialization failure", "message": "' + str(e).replace('"', '\\"') + '"}'
            }
        handler = basic_handler
        app = None

# CRITICAL: Ensure handler is ALWAYS defined
if handler is None:
    sys.stderr.write("⚠️ Handler is None, creating final fallback\n")
    sys.stderr.flush()
    
    def fallback_handler(request):
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "No handler available", "status": "failed"}'
        }
    handler = fallback_handler

sys.stderr.write("=" * 60 + "\n")
sys.stderr.write("✅ Handler exported for Vercel\n")
sys.stderr.write(f"Final handler type: {type(handler).__name__}\n")
sys.stderr.write("=" * 60 + "\n")
sys.stderr.flush()

# Export handler for Vercel
# Vercel will use this handler variable

