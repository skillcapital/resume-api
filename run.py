"""
Quick start script for AI Resume Builder
"""
import uvicorn
import logging

# Configure logging before starting uvicorn
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("=" * 60)
    print("Starting AI Resume Builder API...")
    print("Server will be available at: http://0.0.0.0:8000")
    print("API Documentation: http://0.0.0.0:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True  # Enable access logs
    )

