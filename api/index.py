"""
Vercel serverless function entry point for FastAPI app.
This file serves as the entry point for Vercel's Python runtime.
"""
import sys
import os
import traceback

# Try to configure logging, but don't fail if it doesn't work
try:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
except Exception:
    # If logging fails, create a dummy logger
    class DummyLogger:
        def info(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
    logger = DummyLogger()

# Add parent directory to Python path
# This allows importing the 'app' module from the project root
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Current directory: {current_dir}")
    logger.info(f"Parent directory: {parent_dir}")
except Exception as e:
    logger.error(f"Error setting up paths: {str(e)}")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

# Initialize handler variable
handler = None
error_app = None
error_msg = None

try:
    logger.info("Attempting to import app.main...")
    # Import the FastAPI application
    from app.main import app
    
    logger.info("Successfully imported app.main")
    # Vercel Python runtime requires 'handler' to be exported
    # For ASGI applications like FastAPI, we export the app directly
    handler = app
    logger.info("Handler initialized successfully")
    
except Exception as e:
    # Catch ALL exceptions (not just ImportError) for better debugging
    error_msg = f"Failed to initialize FastAPI app: {str(e)}\n{traceback.format_exc()}"
    logger.error(f"Import error: {error_msg}")
    
    # Create a minimal error handler that shows the actual error
    try:
        logger.info("Creating error handler app...")
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        error_app = FastAPI(title="Error Handler")
        
        @error_app.get("/{full_path:path}")
        @error_app.post("/{full_path:path}")
        @error_app.put("/{full_path:path}")
        @error_app.delete("/{full_path:path}")
        @error_app.get("/")
        async def error_handler(full_path: str = "/"):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Application initialization failed",
                    "message": error_msg,
                    "path": full_path,
                    "python_path": sys.path,
                    "current_dir": current_dir,
                    "parent_dir": parent_dir
                }
            )
        
        handler = error_app
        logger.info("Error handler app created successfully")
    except Exception as fallback_error:
        logger.error(f"Failed to create error handler: {str(fallback_error)}")
        # If even error handler fails, create a basic one
        def basic_handler(request):
            return {
                "statusCode": 500,
                "body": f"Critical error: {str(e)}\nFallback error: {str(fallback_error)}"
            }
        handler = basic_handler

# Ensure handler is always defined
if handler is None:
    logger.error("Handler is None, creating default handler")
    def default_handler(request):
        return {"statusCode": 500, "body": "Handler not initialized"}
    handler = default_handler

try:
    logger.info(f"Final handler type: {type(handler)}")
except Exception:
    pass

# Export handler for Vercel (required)
# Vercel Python runtime looks for 'handler' or 'app'
# Ensure these are always defined, even if initialization failed
if handler is None:
    # Last resort: create a minimal working handler
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        handler = FastAPI(title="Minimal Handler")
        @handler.get("/{full_path:path}")
        @handler.get("/")
        async def minimal_handler(full_path: str = "/"):
            return JSONResponse(
                status_code=500,
                content={"error": "Handler initialization failed", "path": full_path}
            )
    except Exception:
        # If even this fails, create a basic function handler
        def handler(request):
            return {"statusCode": 500, "body": "Critical initialization failure"}

app = handler

