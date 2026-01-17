# GitHub Actions Deployment - Complete Setup Guide

This guide shows you exactly what you need to deploy both frontend and backend using GitHub Actions.

---

## 📋 Required Secrets

You need to add these secrets in your GitHub repository:

**Go to**: `https://github.com/safishamsi/CDKG/settings/secrets/actions`

Click **"New repository secret"** for each:

### For Frontend (Vercel)

1. **`VERCEL_TOKEN`**
   - Get from: https://vercel.com/account/tokens
   - Click "Create Token"
   - Name: `github-actions`
   - Scope: Full Account
   - Copy the token

2. **`VERCEL_ORG_ID`**
   - Get from: https://vercel.com/dashboard
   - Click on your team/account name (top right)
   - Go to Settings → General
   - Copy "Team ID" (this is your Org ID)

3. **`VERCEL_PROJECT_ID`**
   - Get from: https://vercel.com/dashboard
   - Click on your project (cdkg)
   - Go to Settings → General
   - Copy "Project ID"

4. **`VITE_API_URL`** (Optional but recommended)
   - Your backend URL (e.g., `https://your-backend.railway.app` or `https://your-backend.onrender.com`)
   - If not set, frontend will use default or you can set it in Vercel dashboard

### For Backend (Railway)

1. **`RAILWAY_TOKEN`**
   - Get from: https://railway.app/account/tokens
   - Click "New Token"
   - Name: `github-actions`
   - Copy the token

2. **`RAILWAY_SERVICE`** (Optional)
   - Service name in Railway (default: `backend`)
   - Only needed if your service has a different name

---

## 🚀 Step-by-Step Setup

### Step 1: Get Vercel Secrets

1. **Go to Vercel**: https://vercel.com/account/tokens
2. **Create Token**:
   ```
   Name: github-actions
   Scope: Full Account
   ```
3. **Copy Token** → Add to GitHub as `VERCEL_TOKEN`

4. **Get Org ID**:
   - Go to: https://vercel.com/dashboard
   - Click your team name (top right)
   - Settings → General
   - Copy "Team ID" → Add to GitHub as `VERCEL_ORG_ID`

5. **Get Project ID**:
   - Go to: https://vercel.com/dashboard
   - Click your project (cdkg)
   - Settings → General
   - Copy "Project ID" → Add to GitHub as `VERCEL_PROJECT_ID`

### Step 2: Get Railway Secrets

1. **Go to Railway**: https://railway.app/account/tokens
2. **Create Token**:
   ```
   Name: github-actions
   ```
3. **Copy Token** → Add to GitHub as `RAILWAY_TOKEN`

### Step 3: Add Secrets to GitHub

1. **Go to**: https://github.com/safishamsi/CDKG/settings/secrets/actions
2. **Click**: "New repository secret"
3. **Add each secret**:
   - Name: `VERCEL_TOKEN` → Value: (paste token)
   - Name: `VERCEL_ORG_ID` → Value: (paste org ID)
   - Name: `VERCEL_PROJECT_ID` → Value: (paste project ID)
   - Name: `RAILWAY_TOKEN` → Value: (paste token)
   - Name: `VITE_API_URL` → Value: (your backend URL)

### Step 4: Create Projects (If Not Already Created)

#### Create Vercel Project

1. **Go to**: https://vercel.com/dashboard
2. **Add New Project**
3. **Import from GitHub**: Select `safishamsi/CDKG`
4. **Configure**:
   - Root Directory: `frontend`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Add Environment Variable**: `VITE_API_URL` = (your backend URL)
6. **Deploy** (this creates the project)

#### Create Railway Project

1. **Go to**: https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. **Select**: `safishamsi/CDKG`
4. **Configure**:
   - Build Command: `pip install -r requirements_youtube.txt && python -m spacy download en_core_web_sm`
   - Start Command: `uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables**:
   - `NEO4J_URI`
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`
   - `ANTHROPIC_API_KEY`
   - `YOUTUBE_API_KEY`
6. **Deploy** (this creates the service)

---

## ✅ Verify Setup

### Check Secrets Are Set

1. Go to: https://github.com/safishamsi/CDKG/settings/secrets/actions
2. You should see:
   - ✅ `VERCEL_TOKEN`
   - ✅ `VERCEL_ORG_ID`
   - ✅ `VERCEL_PROJECT_ID`
   - ✅ `RAILWAY_TOKEN`
   - ✅ `VITE_API_URL` (optional)

### Test Workflows

1. **Make a small change** (or push existing code)
2. **Go to**: https://github.com/safishamsi/CDKG/actions
3. **Check workflows**:
   - "Deploy Frontend to Vercel" should run
   - "Deploy Backend to Railway" should run
4. **Both should succeed** ✅

---

## 🔄 How It Works

### Automatic Deployment

1. **You push to `main` branch**
2. **GitHub Actions triggers**:
   - Frontend workflow → Deploys to Vercel
   - Backend workflow → Deploys to Railway
3. **Both deploy automatically** ✅

### Manual Deployment

You can also trigger manually:
1. Go to: https://github.com/safishamsi/CDKG/actions
2. Select workflow (e.g., "Deploy Frontend to Vercel")
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

---

## 🐛 Troubleshooting

### Workflow Fails: "Secret not found"

- **Check**: Secrets are set in GitHub
- **Go to**: Settings → Secrets and variables → Actions
- **Verify**: All required secrets are present

### Vercel Deployment Fails

- **Check**: `VERCEL_TOKEN` is valid
- **Check**: `VERCEL_ORG_ID` matches your team
- **Check**: `VERCEL_PROJECT_ID` matches your project
- **Verify**: Project exists in Vercel

### Railway Deployment Fails

- **Check**: `RAILWAY_TOKEN` is valid
- **Check**: Service exists in Railway
- **Check**: `RAILWAY_SERVICE` name is correct (or leave empty for default)

### Frontend Can't Connect to Backend

- **Check**: `VITE_API_URL` is set correctly
- **Check**: Backend is deployed and accessible
- **Check**: Backend URL is correct (no trailing slash)

---

## 📝 Quick Checklist

- [ ] Created Vercel token → Added as `VERCEL_TOKEN`
- [ ] Got Vercel Org ID → Added as `VERCEL_ORG_ID`
- [ ] Got Vercel Project ID → Added as `VERCEL_PROJECT_ID`
- [ ] Created Railway token → Added as `RAILWAY_TOKEN`
- [ ] Set `VITE_API_URL` → Your backend URL
- [ ] Created Vercel project (if not exists)
- [ ] Created Railway project (if not exists)
- [ ] Tested workflows → Both succeed

---

## 🎯 Summary

**What you need:**
1. 4-5 GitHub secrets (tokens and IDs)
2. Vercel project created
3. Railway project created

**Result:**
- Every push to `main` → Auto-deploys frontend and backend
- No manual deployment needed
- Everything automated via GitHub Actions

---

**Ready to set up?** Follow the steps above and you'll have automated deployment working! 🚀

