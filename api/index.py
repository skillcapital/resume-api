"""
Vercel serverless function entry point for FastAPI app.
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Vercel expects a handler function for ASGI apps
handler = app

