import os
import logging
import sys
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.routes_resume import router as resume_router
from app.core.config import FRONTEND_URL

# Configure logging - only if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),  # Output to stderr (works for both local and Vercel)
        ],
        force=True  # Override any existing configuration
    )

# Set specific loggers to INFO level to ensure they show logs
for logger_name in ["app", "app.api", "app.services", "app.api.routes_resume", "app.services.pdf_exporter", "app.services.langchain_ai"]:
    logger_obj = logging.getLogger(logger_name)
    logger_obj.setLevel(logging.INFO)
    # Ensure it has a handler if it doesn't propagate
    if not logger_obj.handlers and logger_obj.propagate:
        pass  # Will use root logger's handler

# Create root logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("=" * 60)
logger.info("AI Resume Builder API Starting...")
logger.info("Logging configured - INFO level")
logger.info("=" * 60)

app = FastAPI(
    title="AI Resume Builder",
    description="Build and improve resumes with AI assistance",
    version="1.0.0"
)

# Custom exception handler for JSON decode errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors to provide more helpful error messages.
    """
    logger = logging.getLogger(__name__)
    
    errors = exc.errors()
    
    # Check if it's a JSON decode error
    for error in errors:
        if error.get("type") == "json_invalid":
            error_msg = error.get("ctx", {}).get("error", "Invalid JSON")
            error_pos = error.get("loc", [])
            
            # Try to get the body to show context around the error
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode('utf-8', errors='replace')
                error_position = error_pos[1] if len(error_pos) > 1 else 0
                
                # Show context around the error (50 chars before and after)
                start = max(0, error_position - 50)
                end = min(len(body_text), error_position + 50)
                context = body_text[start:end]
                
                # Mark the error position
                relative_pos = error_position - start
                marked_context = (
                    context[:relative_pos] + 
                    " <-- ERROR HERE --> " + 
                    context[relative_pos:]
                )
                
                logger.error(f"JSON decode error at position {error_position}")
                logger.error(f"Context: {marked_context}")
                
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "detail": f"Invalid JSON in request body. {error_msg}",
                        "error_type": "json_decode_error",
                        "error_position": error_position,
                        "context_around_error": marked_context,
                        "location": list(error_pos),
                        "help": "Please check your JSON syntax. Common issues: missing commas, unclosed brackets, or invalid characters.",
                        "example": {
                            "resume_id": "valid-uuid-here",
                            "tone": "professional",
                            "name": "John Doe",
                            "email": "john@example.com"
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"Could not extract body context: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "detail": f"Invalid JSON in request body. {error_msg}",
                        "error_type": "json_decode_error",
                        "location": list(error_pos),
                        "help": "Please check your JSON syntax. Common issues: missing commas, unclosed brackets, or invalid characters.",
                        "example": {
                            "resume_id": "valid-uuid-here",
                            "tone": "professional",
                            "name": "John Doe",
                            "email": "john@example.com"
                        }
                    }
                )
    
    # For other validation errors, return the standard format
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )

# Configure CORS with preview frontend URL
allowed_origins = [
   # "https://supabase-skillcapital-lms-git-2c784d-tech-kdigitalais-projects.vercel.app",  
   "https://dev.my.skillcapital.ai",# Preview frontend URL
    FRONTEND_URL,  # From environment variable (for future production URL)
    "http://localhost:3000",  # Local development
    "http://127.0.0.1:3000",  # Alternative localhost
]

# Remove duplicates while preserving order
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware to debug routing issues
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    import logging
    logger = logging.getLogger(__name__)
    
    method = request.method
    path = request.url.path
    logger.info(f"Incoming request: {method} {path}")
    
    # Log headers that might affect routing
    if "content-type" in request.headers:
        logger.info(f"Content-Type: {request.headers.get('content-type')}")
    
    response = await call_next(request)
    
    logger.info(f"Response status: {response.status_code} for {method} {path}")
    return response

app.include_router(resume_router, prefix="/api/v1/resumes", tags=["resumes"])

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("FastAPI application started")
    logger.info(f"API Documentation available at: /docs")
    logger.info(f"Health check available at: /health")

@app.get("/")
def root():
    return {"message": "AI Resume Builder is running 🚀", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/debug/json-test")
async def debug_json_test(request: Request):
    """
    Debug endpoint to test JSON parsing and see what's being sent.
    This helps identify JSON syntax errors.
    """
    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8')
        
        # Try to parse as JSON
        import json
        try:
            parsed_json = json.loads(body_text)
            return {
                "status": "success",
                "message": "JSON is valid",
                "body_length": len(body_text),
                "parsed_keys": list(parsed_json.keys()) if isinstance(parsed_json, dict) else "Not a dict",
                "preview": body_text[:500] + "..." if len(body_text) > 500 else body_text
            }
        except json.JSONDecodeError as e:
            # Show where the error is
            error_pos = e.pos
            start = max(0, error_pos - 50)
            end = min(len(body_text), error_pos + 50)
            context = body_text[start:end]
            
            return {
                "status": "error",
                "message": "Invalid JSON detected",
                "error": str(e),
                "error_position": error_pos,
                "context_around_error": context,
                "body_length": len(body_text),
                "preview": body_text[:1000] + "..." if len(body_text) > 1000 else body_text
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading request: {str(e)}"
        }
