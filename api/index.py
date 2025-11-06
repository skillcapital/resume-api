"""
Vercel serverless function entry point for FastAPI app.
This file serves as the entry point for Vercel's Python runtime.
"""
import sys
import os
import traceback
import logging

# Configure logging to help debug issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to Python path
# This allows importing the 'app' module from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

logger.info(f"Python path: {sys.path}")
logger.info(f"Current directory: {current_dir}")
logger.info(f"Parent directory: {parent_dir}")

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

logger.info(f"Final handler type: {type(handler)}")

# Export handler for Vercel (required)
# Vercel Python runtime looks for 'handler' or 'app'
app = handler

