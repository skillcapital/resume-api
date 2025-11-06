# Vercel Deployment Guide

This guide explains how to deploy your FastAPI backend to Vercel with optimized package size.

## Files Created

1. **`.vercelignore`** - Excludes unnecessary files from deployment (venv, cache, etc.)
2. **`requirements-vercel.txt`** - Minimal dependencies (removed pandas, numpy, streamlit, etc.)
3. **`vercel.json`** - Vercel configuration
4. **`api/index.py`** - Vercel serverless function entry point

## Size Reduction

The original `requirements.txt` had **109 packages** including:
- ❌ `pandas` (large, not used)
- ❌ `numpy` (large, not used)
- ❌ `streamlit` (not needed for API)
- ❌ `altair`, `pydeck` (not needed)
- ❌ `weasyprint` (replaced with `xhtml2pdf` which is smaller)

The new `requirements-vercel.txt` has **~40 essential packages** only.

## Deployment Steps

### 1. Update Vercel Project Settings

In Vercel Dashboard → Project Settings → General:

- **Install Command**: `pip install -r requirements-vercel.txt`
- **Build Command**: Leave empty or `echo 'No build needed'`
- **Output Directory**: `.` (root)

### 2. Environment Variables

Make sure to set these in Vercel Dashboard → Settings → Environment Variables:

```
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key
OPENAI_API_KEY=your-openai-key
SUPABASE_BUCKET_UPLOADS=uploads
SUPABASE_BUCKET_EXPORTS=exports
```

### 3. Deploy

```bash
# Push to your repository
git add .
git commit -m "Optimize for Vercel deployment"
git push

# Vercel will automatically deploy
```

Or deploy via Vercel CLI:
```bash
vercel --prod
```

## Testing Locally

Before deploying, test with the minimal requirements:

```bash
# Create a test virtual environment
python -m venv venv-test
venv-test\Scripts\activate  # Windows
# or
source venv-test/bin/activate  # Linux/Mac

# Install minimal requirements
pip install -r requirements-vercel.txt

# Test the app
python run.py
```

## Troubleshooting

### If deployment still exceeds 250MB:

1. **Check `.vercelignore`** - Make sure `venv/` is excluded
2. **Remove unused dependencies** - Review `requirements-vercel.txt`
3. **Consider alternatives**:
   - Use Render (500MB limit) instead
   - Split into microservices
   - Use external services for heavy operations

### If `langchain-openai` is missing:

The package `langchain-openai` is required. If it's not found, try:
```bash
pip install langchain-openai
```

### If imports fail:

Make sure all imports in your code match the packages in `requirements-vercel.txt`.

## Important Notes

- ✅ The code uses `xhtml2pdf` (not `weasyprint`) for PDF generation
- ✅ `langchain-openai` is required for AI functionality
- ✅ All Supabase packages are included
- ✅ CORS is configured in `app/main.py` - update with your frontend URL

## Next Steps

1. Update CORS in `app/main.py` with your production frontend URL
2. Test the deployment
3. Monitor function size in Vercel dashboard
4. If still too large, consider deploying to Render instead

