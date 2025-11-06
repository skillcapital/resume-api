# FastAPI Vercel Deployment Checklist ✅

## ✅ Configuration Files (All Set)

1. **`vercel.json`** - Vercel configuration with Python runtime
2. **`api/index.py`** - Serverless function entry point with error handling
3. **`requirements.txt`** - Optimized dependencies for production (~40 packages)
4. **`requirements-dev.txt`** - Full dependencies for local development (109 packages)
5. **`.vercelignore`** - Excludes unnecessary files (venv, cache, etc.)

## 🔧 Vercel Dashboard Settings

### Project Settings → General:
- **Framework Preset**: `Other`
- **Root Directory**: `.` (leave empty or set to `.`)
- **Build Command**: Leave **EMPTY**
- **Output Directory**: Leave **EMPTY**
- **Install Command**: Leave empty (Vercel auto-detects `requirements.txt`)

### Environment Variables (Settings → Environment Variables):
```
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key
OPENAI_API_KEY=your-openai-key
SUPABASE_BUCKET_UPLOADS=uploads
SUPABASE_BUCKET_EXPORTS=exports
```

## 📋 Pre-Deployment Checklist

- [ ] All files committed to Git
- [ ] `vercel.json` is in root directory
- [ ] `api/index.py` exists and exports `handler`
- [ ] `requirements.txt` is in root directory (optimized for production)
- [ ] `requirements-dev.txt` is in root directory (for local development)
- [ ] `.vercelignore` is in root directory
- [ ] Environment variables set in Vercel Dashboard
- [ ] CORS updated in `app/main.py` with production frontend URL

## 🚀 Deployment Steps

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Configure FastAPI for Vercel deployment"
   git push
   ```

2. **Vercel will automatically deploy** (if connected to GitHub)

3. **Or deploy manually:**
   ```bash
   vercel --prod
   ```

## ✅ Verification

After deployment, test these endpoints:

1. **Health Check:**
   ```
   GET https://your-app.vercel.app/health
   Expected: {"status": "healthy"}
   ```

2. **Root Endpoint:**
   ```
   GET https://your-app.vercel.app/
   Expected: {"message": "AI Resume Builder is running 🚀", "docs": "/docs"}
   ```

3. **API Docs:**
   ```
   GET https://your-app.vercel.app/docs
   Expected: Swagger UI documentation
   ```

4. **API Endpoint:**
   ```
   GET https://your-app.vercel.app/api/v1/resumes/templates
   Expected: List of available templates
   ```

## 🐛 Troubleshooting

### If deployment fails:

1. **Check Vercel Build Logs:**
   - Go to Vercel Dashboard → Deployments → Click failed deployment
   - Check for import errors or missing dependencies

2. **Verify Python Detection:**
   - Vercel should detect Python automatically
   - If not, ensure `requirements.txt` exists in root

3. **Check Function Size:**
   - Should be under 250MB
   - Check `.vercelignore` is excluding `venv/`

4. **Import Errors:**
   - Verify all imports in `requirements.txt`
   - Check `api/index.py` can import `app.main`

### Common Issues:

**Issue:** "Module not found"
- **Solution:** Check `requirements.txt` has all dependencies

**Issue:** "Handler not found"
- **Solution:** Ensure `api/index.py` exports `handler = app`

**Issue:** "Build timeout"
- **Solution:** Check dependencies size, remove unused packages

**Issue:** "Function too large"
- **Solution:** Review `.vercelignore`, ensure `venv/` is excluded

## 📝 Important Notes

- ✅ Uses `@vercel/python` runtime
- ✅ All routes rewrite to `api/index.py`
- ✅ Error handling included in `api/index.py`
- ✅ Optimized dependencies (removed pandas, numpy, streamlit)
- ✅ CORS configured for production

## 🔄 After Successful Deployment

1. Update CORS in `app/main.py` with your actual frontend URL
2. Test all API endpoints
3. Monitor function logs in Vercel Dashboard
4. Set up custom domain (optional)

---

**Status:** ✅ Ready for deployment

