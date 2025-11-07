"""
Vercel serverless function entry point for FastAPI app.
Uses Mangum adapter for proper ASGI compatibility with Vercel.
"""
import sys
import os
import traceback

# Write errors to stderr immediately (Vercel captures this)
def log_error(message):
    """Log error to stderr for Vercel logs"""
    try:
        sys.stderr.write(f"[ERROR] {message}\n")
        sys.stderr.flush()
    except:
        pass

def log_info(message):
    """Log info to stderr for Vercel logs"""
    try:
        sys.stderr.write(f"[INFO] {message}\n")
        sys.stderr.flush()
    except:
        pass

log_info("=" * 80)
log_info("Starting Vercel Python handler initialization with Mangum")
log_info(f"Python version: {sys.version}")

# Add parent directory to Python path
# This allows importing the 'app' module from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    log_info(f"Added {parent_dir} to sys.path")

# Initialize handler variable
handler = None

try:
    log_info("Attempting to import app.main...")
    # Import the FastAPI application
    from app.main import app
    
    log_info("✅ Successfully imported app.main")
    log_info(f"App type: {type(app).__name__}")
    
    # Import Mangum adapter
    log_info("Importing Mangum adapter...")
    from mangum import Mangum
    
    # Wrap FastAPI app with Mangum for Vercel compatibility
    # lifespan="off" disables lifespan events (not needed for serverless)
    handler = Mangum(app, lifespan="off")
    
    log_info("✅ Handler created with Mangum adapter")
    log_info(f"Handler type: {type(handler).__name__}")
    
except ImportError as e:
    error_msg = f"ImportError: {str(e)}\n{traceback.format_exc()}"
    log_error(error_msg)
    
    # Try to create a minimal error handler with Mangum
    try:
        log_info("Creating error handler app with Mangum...")
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from mangum import Mangum
        
        error_app = FastAPI(title="Error Handler")
        
        @error_app.get("/{full_path:path}")
        @error_app.post("/{full_path:path}")
        @error_app.put("/{full_path:path}")
        @error_app.delete("/{full_path:path}")
        @error_app.patch("/{full_path:path}")
        async def error_handler(full_path: str):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Application initialization failed - ImportError",
                    "message": str(e),
                    "path": full_path,
                    "python_path": sys.path,
                    "current_dir": current_dir,
                    "parent_dir": parent_dir,
                    "traceback": traceback.format_exc()
                }
            )
        
        handler = Mangum(error_app, lifespan="off")
        log_info("✅ Error handler app created with Mangum")
    except Exception as fallback_error:
        log_error(f"Failed to create error handler: {fallback_error}")
        log_error(traceback.format_exc())
        # Last resort: basic function handler
        def basic_handler(request):
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": f'{{"error": "ImportError", "message": "{str(e)}", "fallback_error": "{str(fallback_error)}"}}'
            }
        handler = basic_handler
        
except Exception as e:
    # Catch ALL other exceptions
    error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
    log_error(error_msg)
    
    # Create a minimal error handler that shows the actual error
    try:
        log_info("Creating error handler for unexpected error with Mangum...")
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from mangum import Mangum
        
        error_app = FastAPI(title="Error Handler")
        
        @error_app.get("/{full_path:path}")
        @error_app.post("/{full_path:path}")
        @error_app.put("/{full_path:path}")
        @error_app.delete("/{full_path:path}")
        @error_app.patch("/{full_path:path}")
        async def error_handler(full_path: str):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Application initialization failed",
                    "message": str(e),
                    "path": full_path,
                    "python_path": sys.path,
                    "current_dir": current_dir,
                    "parent_dir": parent_dir,
                    "traceback": traceback.format_exc()
                }
            )
        
        handler = Mangum(error_app, lifespan="off")
        log_info("✅ Error handler app created with Mangum")
    except Exception as fallback_error:
        log_error(f"Failed to create error handler: {fallback_error}")
        log_error(traceback.format_exc())
        # If even error handler fails, create a basic one
        def basic_handler(request):
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": f'{{"error": "Critical error", "message": "{str(e)}", "fallback_error": "{str(fallback_error)}"}}'
            }
        handler = basic_handler

# Ensure handler is always defined
if handler is None:
    log_error("Handler is None! Creating default handler")
    def default_handler(request):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Handler not initialized"}'
        }
    handler = default_handler

log_info(f"✅ Final handler type: {type(handler).__name__}")
log_info("=" * 80)

# CRITICAL: Export handler for Vercel
# This MUST exist at module level
