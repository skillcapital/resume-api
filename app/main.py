from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_resume import router as resume_router

app = FastAPI(
    title="AI Resume Builder",
    description="Build and improve resumes with AI assistance",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
#app.add_middleware(
   # CORSMiddleware,
    #allow_origins=[
       # "http://localhost:3000",
        #"http://127.0.0.1:3000",
        #"http://localhost:3001",
        #"http://127.0.0.1:3001",
        #"http://localhost:8000",
        #"http://127.0.0.1:8000",
    #],
    #allow_origin_regex=r"http://localhost:\d+",  # Allow any localhost port
    #allow_credentials=True,
    #allow_methods=["*"],
    #allow_headers=["*"],

    # Configure CORS for production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",  # Add your production frontend URL
        "http://localhost:3000",  # Keep for local development
    ],
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

