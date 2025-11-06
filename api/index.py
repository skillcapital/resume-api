"""
Vercel serverless function entry point for FastAPI app.
This file serves as the entry point for Vercel's Python runtime.
"""
import sys
import os

# Add parent directory to Python path
# This allows importing the 'app' module from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Import the FastAPI application
    from app.main import app
    
    # Vercel Python runtime requires 'handler' to be exported
    # For ASGI applications like FastAPI, we export the app directly
    handler = app
    
except ImportError as e:
    # Error handling for deployment debugging
    import traceback
    error_msg = f"Failed to import FastAPI app: {str(e)}\n{traceback.format_exc()}"
    
    # Create a minimal error handler
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    error_app = FastAPI()
    
    @error_app.get("/{full_path:path}")
    async def error_handler(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application import failed",
                "message": error_msg,
                "path": full_path
            }
        )
    
    handler = error_app

