# Quick Start Guide 🚀

## Step 1: Set Up Environment Variables

1. Copy the example env file:
```bash
copy .env.example .env
```

2. Edit `.env` and add your credentials:
   - Get your **Supabase URL** and **Service Key** from: https://supabase.com/dashboard
   - Get your **OpenAI API Key** from: https://platform.openai.com/api-keys

## Step 2: Set Up Supabase Database

1. Go to your Supabase project dashboard
2. Open the **SQL Editor**
3. Copy and paste the contents of `SUPABASE_SETUP.sql`
4. Click **Run**

5. Create Storage Buckets:
   - Go to **Storage** in Supabase dashboard
   - Create bucket: `uploads` (Public: Yes)
   - Create bucket: `exports` (Public: Yes)

## Step 3: Run the Application

```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Run the app
python run.py
```

Or:
```bash
uvicorn app.main:app --reload
```

## Step 4: Test the API

Visit: **http://localhost:8000/docs**

You'll see the interactive API documentation (Swagger UI).

### Test Endpoints:

1. **Health Check**: `GET /health`
2. **Upload Resume**: `POST /api/v1/resumes/upload`
3. **Improve Resume**: `POST /api/v1/resumes/improve`
4. **Tailor Resume**: `POST /api/v1/resumes/tailor`
5. **Export PDF**: `GET /api/v1/resumes/export/{resume_id}`

## Example Workflow

```bash
# 1. Upload a PDF resume
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -F "file=@resume.pdf"

# Response: {"resume_id": "xxx", "parsed_text": "...", "status": "success"}

# 2. Improve the resume with AI
curl -X POST "http://localhost:8000/api/v1/resumes/improve" \
  -F "resume_id=xxx"

# 3. Tailor for a job
curl -X POST "http://localhost:8000/api/v1/resumes/tailor" \
  -F "resume_id=xxx" \
  -F "job_description=Senior Python Developer position..."

# 4. Export as PDF
curl -X GET "http://localhost:8000/api/v1/resumes/export/xxx"
```

## Troubleshooting

### Error: "Supabase client not initialized"
- Check your `.env` file has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### Error: "OpenAI API key not found"
- Check your `.env` file has `OPENAI_API_KEY`

### Error: "Table not found"
- Run the SQL setup from `SUPABASE_SETUP.sql` in your Supabase SQL Editor

### Error: "Bucket not found"
- Create the storage buckets (`uploads` and `exports`) in Supabase Dashboard > Storage

## Next Steps

- Customize the resume template: `app/templates/resume_default.html`
- Add authentication (JWT tokens)
- Add user accounts
- Add resume templates
- Add email notifications

