import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_resume import router as resume_router
from app.core.config import FRONTEND_URL

app = FastAPI(
    title="AI Resume Builder",
    description="Build and improve resumes with AI assistance",
    version="1.0.0"
)

# Configure CORS with preview frontend URL
allowed_origins = [
    "https://supabase-skillcapital-lms-git-2c784d-tech-kdigitalais-projects.vercel.app",  # Preview frontend URL
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


app.include_router(resume_router, prefix="/api/v1/resumes", tags=["resumes"])

@app.get("/")
def root():
    return {"message": "AI Resume Builder is running 🚀", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
