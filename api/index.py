"""
Vercel serverless function entry point for FastAPI app.
"""
import sys
import os

# Add parent directory to path so we can import app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the FastAPI app
from app.main import app

# Vercel Python runtime expects 'handler' or 'app' to be exported
# For ASGI apps like FastAPI, we export the app directly
handler = app
app = app  # Also export as 'app' for compatibility

