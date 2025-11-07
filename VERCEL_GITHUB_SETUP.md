# Vercel GitHub Auto-Deployment Setup Guide

## ✅ Current Status
- ✅ `.vercel` folder is ignored in `.gitignore`
- ✅ `vercel.json` is properly configured
- ✅ No Vercel CLI dependencies in project

## 🔧 Steps to Enable GitHub Auto-Deployment

### Step 1: Verify GitHub Connection in Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project (`ai-resume-builder`)
3. Go to **Settings** → **Git**
4. Verify:
   - ✅ Shows "Connected to GitHub"
   - ✅ Shows your repository URL: `github.com/yourusername/ai-resume-builder`
   - ✅ Production Branch is set to `main` (or your default branch)

### Step 2: If NOT Connected, Connect GitHub

1. In **Settings** → **Git**, click **"Connect Git Repository"**
2. Authorize Vercel to access your GitHub account
3. Select your repository: `ai-resume-builder`
4. Choose production branch: `main` (or `master`)
5. Click **"Connect"**

### Step 3: Verify Webhook in GitHub

1. Go to your GitHub repository
2. Go to **Settings** → **Webhooks**
3. Look for a Vercel webhook (should show `vercel.com` in URL)
4. If missing, it will be created automatically when you connect in Vercel

### Step 4: Test Auto-Deployment

1. Make a small change in your code:
   ```bash
   echo "# Test auto-deploy" >> README.md
   ```

2. Commit and push:
   ```bash
   git add README.md
   git commit -m "Test: Verify auto-deployment"
   git push origin main
   ```

3. Check Vercel Dashboard → **Deployments**
   - You should see a new deployment starting automatically
   - It should show "Triggered by GitHub push"

## 🚫 Important Notes

- **Vercel CLI**: Having Vercel CLI installed globally does NOT prevent GitHub auto-deployment
- **`.vercel` folder**: This folder is now ignored and won't interfere
- **Both methods work**: You can use both CLI (`vercel`) and GitHub auto-deploy

## 🔍 Troubleshooting

### If auto-deployment still doesn't work:

1. **Check Vercel Dashboard → Settings → Git**
   - Must show your GitHub repo connected
   - Production branch must match your default branch

2. **Check GitHub Webhooks**
   - Go to GitHub repo → Settings → Webhooks
   - Vercel webhook should exist and show recent deliveries
   - If webhook shows errors, reconnect in Vercel

3. **Verify Branch Name**
   - Make sure you're pushing to the branch set as "Production Branch" in Vercel
   - Usually `main` or `master`

4. **Check Deployment Settings**
   - Vercel Dashboard → Settings → General
   - Root Directory: Should be empty or `/`
   - Framework Preset: Other
   - Build Command: (empty - auto-detected)
   - Output Directory: (empty)

5. **Manual Trigger Test**
   - Vercel Dashboard → Deployments → Click "Redeploy"
   - If manual deploy works but auto-deploy doesn't, it's a GitHub connection issue

## ✅ Success Indicators

When working correctly, you should see:
- ✅ New deployments appear automatically after `git push`
- ✅ Deployment shows "Triggered by GitHub push"
- ✅ Vercel Dashboard → Settings → Git shows your GitHub repo
- ✅ GitHub webhook shows successful deliveries

## 📝 Next Steps

After verifying the connection:
1. Push your optimized code to GitHub
2. Watch Vercel Dashboard for automatic deployment
3. Your FastAPI backend will be live automatically!

