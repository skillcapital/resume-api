"""
Vercel entry point - simple wrapper that imports from app.main
This allows Vercel to find the entry point at root level while keeping
all your code organized in the app/ package.
"""
import sys
import os
import traceback

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print("=" * 50, file=sys.stderr)
print("Root main.py: Starting import from app.main", file=sys.stderr)
print("Python path:", sys.path, file=sys.stderr)
print("Current directory:", current_dir, file=sys.stderr)
print("=" * 50, file=sys.stderr)

try:
    # Import the app from app.main
    from app.main import app, handler
    
    # Ensure handler is exported for Vercel
    if 'handler' not in dir() or handler is None:
        handler = app
    
    print("✅ Successfully imported app from app.main", file=sys.stderr)
    print("✅ Handler ready for Vercel", file=sys.stderr)
    
except Exception as e:
    print("❌ Failed to import app.main:", str(e), file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    
    # Fallback minimal error app
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="Error Handler")
    
    @app.get("/{full_path:path}")
    @app.get("/")
    async def error_handler(full_path: str = "/"):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to import application",
                "message": str(e),
                "traceback": traceback.format_exc(),
                "python_path": sys.path,
                "current_dir": current_dir
            }
        )
    
    handler = app

# Vercel requires 'handler' or 'app' to be exported
sys.stdout.flush()
sys.stderr.flush()