"""
Vercel serverless function entry point for FastAPI app.
Vercel natively supports ASGI applications, so we export the app directly.
"""
import sys
import os

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import and export FastAPI app directly
# Vercel natively supports ASGI applications like FastAPI
try:
    from app.main import app
    # Export the app directly - Vercel handles ASGI natively
    handler = app
    
except Exception as e:
    # If import fails, create minimal error handler
    import traceback
    
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        error_app = FastAPI()
        
        @error_app.get("/{full_path:path}")
        @error_app.post("/{full_path:path}")
        @error_app.put("/{full_path:path}")
        @error_app.delete("/{full_path:path}")
        @error_app.patch("/{full_path:path}")
        async def error_handler(full_path: str):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Application failed to initialize",
                    "message": str(e),
                    "type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
        
        handler = error_app
        
    except Exception as fallback_error:
        # Last resort: create a basic function handler
        def basic_handler(request):
            import json
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Critical initialization failure",
                    "primary_error": str(e),
                    "fallback_error": str(fallback_error)
                })
            }
        handler = basic_handler
