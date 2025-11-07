"""
Minimal test - verify Vercel can run Python/FastAPI
"""
import sys
import traceback

# Immediate output to verify Python is running
print("=" * 60, file=sys.stderr)
print("MINIMAL TEST: Python is running!", file=sys.stderr)
print("Python version:", sys.version, file=sys.stderr)
print("=" * 60, file=sys.stderr)
sys.stderr.flush()

try:
    # Try importing FastAPI
    print("Step 1: Importing FastAPI...", file=sys.stderr)
    sys.stderr.flush()
    
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    print("✅ FastAPI imported successfully", file=sys.stderr)
    sys.stderr.flush()
    
    # Create minimal app
    print("Step 2: Creating FastAPI app...", file=sys.stderr)
    sys.stderr.flush()
    
    app = FastAPI(title="Minimal Test")
    
    @app.get("/")
    def root():
        return {"message": "Minimal test working! ✅", "status": "success"}
    
    @app.get("/health")
    def health():
        return {"status": "healthy"}
    
    print("✅ FastAPI app created", file=sys.stderr)
    sys.stderr.flush()
    
except Exception as e:
    print(f"❌ Error: {str(e)}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    
    # Even on error, create a working app
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="Error Handler")
    
    @app.get("/{full_path:path}")
    @app.get("/")
    async def error_handler(full_path: str = "/"):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Initialization error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        )

# Export for Vercel
handler = app
print("✅ Handler exported", file=sys.stderr)
sys.stdout.flush()
sys.stderr.flush()