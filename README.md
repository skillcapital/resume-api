# AI Resume Builder

An intelligent resume builder powered by AI (OpenAI + LangChain), FastAPI, and Supabase.

## Features

- 📄 **PDF Resume Upload** - Upload and parse existing resumes
- 🤖 **AI-Powered Improvement** - Automatically improve resumes using AI
- 🎯 **Job Description Tailoring** - Tailor resumes for specific job postings
- 📥 **PDF Export** - Generate professional PDF resumes
- 💾 **Database Storage** - Store resumes and versions in Supabase

## Tech Stack

- **Backend**: FastAPI
- **AI**: OpenAI (GPT-4o-mini) + LangChain
- **Database**: Supabase (PostgreSQL)
- **PDF Processing**: pdfminer.six, WeasyPrint
- **Templates**: Jinja2

## Setup

### 1. Prerequisites

- Python 3.12+
- Supabase account
- OpenAI API key

### 2. Install Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-openai-api-key
SUPABASE_BUCKET_UPLOADS=uploads
SUPABASE_BUCKET_EXPORTS=exports
```

### 4. Set Up Supabase Database

Run this SQL in your Supabase SQL Editor:

```sql
-- Create resumes table
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create resume_versions table
CREATE TABLE resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    version_type TEXT DEFAULT 'improved',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_resume_versions_resume_id ON resume_versions(resume_id);
CREATE INDEX idx_resume_versions_created_at ON resume_versions(created_at DESC);

-- Create storage buckets (run in Supabase Dashboard > Storage)
-- 1. Create bucket: uploads (public)
-- 2. Create bucket: exports (public)
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

Visit:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## API Endpoints

### Upload Resume
```bash
POST /api/v1/resumes/upload
Content-Type: multipart/form-data
Body: file (PDF)
```

### Improve Resume
```bash
POST /api/v1/resumes/improve
Content-Type: application/x-www-form-urlencoded
Body: resume_id
```

### Tailor Resume
```bash
POST /api/v1/resumes/tailor
Content-Type: application/x-www-form-urlencoded
Body: resume_id, job_description
```

### Export Resume
```bash
GET /api/v1/resumes/export/{resume_id}?version_type=latest
```

### Get Resume
```bash
GET /api/v1/resumes/{resume_id}
```

## Project Structure

```
ai-resume-builder/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes_resume.py    # API routes
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Configuration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── langchain_ai.py    # AI service
│   │   ├── pdf_parser.py       # PDF text extraction
│   │   ├── pdf_exporter.py     # PDF generation
│   │   └── supabase_client.py  # Database client
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   └── templates/
│       └── resume_default.html # Resume template
├── .env                         # Environment variables (not in git)
├── .env.example                 # Example env file
├── .gitignore
├── requirements.txt
└── README.md
```

## Usage Example

1. **Upload a resume PDF**
2. **Get the resume_id from the response**
3. **Improve it with AI**: `/api/v1/resumes/improve`
4. **Tailor for a job**: `/api/v1/resumes/tailor`
5. **Export PDF**: `/api/v1/resumes/export/{resume_id}`

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing with Cursor

Cursor's built-in HTTP Client allows you to test endpoints directly:
1. Right-click on any route in `routes_resume.py`
2. Select "Run Request" or "Test Endpoint"
3. Results appear inline

## License

MIT

# Auto-deploy test
