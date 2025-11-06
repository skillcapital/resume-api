"""
Vercel serverless function entry point for FastAPI app.
This file serves as the entry point for Vercel's Python runtime.
"""
import sys
import os
import traceback

# Add parent directory to Python path
# This allows importing the 'app' module from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Initialize handler variable
handler = None
error_app = None

try:
    # Import the FastAPI application
    from app.main import app
    
    # Vercel Python runtime requires 'handler' to be exported
    # For ASGI applications like FastAPI, we export the app directly
    handler = app
    
except Exception as e:
    # Catch ALL exceptions (not just ImportError) for better debugging
    error_msg = f"Failed to initialize FastAPI app: {str(e)}\n{traceback.format_exc()}"
    
    # Create a minimal error handler that shows the actual error
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        error_app = FastAPI(title="Error Handler")
        
        @error_app.get("/{full_path:path}")
        @error_app.post("/{full_path:path}")
        @error_app.put("/{full_path:path}")
        @error_app.delete("/{full_path:path}")
        async def error_handler(full_path: str):
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
    except Exception as fallback_error:
        # If even error handler fails, create a basic one
        def basic_handler(request):
            return {
                "statusCode": 500,
                "body": f"Critical error: {str(e)}\nFallback error: {str(fallback_error)}"
            }
        handler = basic_handler

# Ensure handler is always defined
if handler is None:
    def default_handler(request):
        return {"statusCode": 500, "body": "Handler not initialized"}
    handler = default_handler

