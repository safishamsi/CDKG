# GitHub Actions Setup Guide

## ⚠️ Workflow Failures

If you see workflow failures, they're likely because required secrets aren't configured. **This is normal and optional** - you can either:

1. **Set up the secrets** (if you want automated deployment)
2. **Disable the workflows** (if you prefer manual deployment)
3. **Use platform auto-deploy** (Vercel/Railway can auto-deploy from GitHub without Actions)

---

## 🔧 Setting Up Secrets

### For Railway Deployment

1. **Go to GitHub Repository**
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"

2. **Add Secrets**:
   - `RAILWAY_TOKEN` - Get from Railway → Settings → Tokens
   - `RAILWAY_SERVICE` (optional) - Service name (default: "backend")

3. **Or use Railway's GitHub integration** (easier):
   - Railway auto-deploys from GitHub
   - No secrets needed in GitHub Actions

### For Vercel Deployment

**Option 1: Use Vercel GitHub Integration (Recommended)**
- Vercel auto-deploys from GitHub
- No GitHub Actions needed
- Just connect Vercel to your GitHub repo

**Option 2: Use GitHub Actions (Optional)**
1. **Go to GitHub Repository**
   - Settings → Secrets and variables → Actions
   - Add secrets:
     - `VERCEL_TOKEN` - Get from Vercel → Settings → Tokens
     - `VERCEL_ORG_ID` - Get from Vercel project settings
     - `VERCEL_PROJECT_ID` - Get from Vercel project settings
     - `VITE_API_URL` - Your backend URL

---

## ✅ Recommended Setup

### Frontend: Vercel Auto-Deploy (No Actions Needed)

1. **Go to Vercel Dashboard**
2. **Import Project from GitHub**
3. **Select your repository**
4. **Configure**:
   - Root Directory: `frontend`
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Add Environment Variable**: `VITE_API_URL`
6. **Deploy**

**Result**: Every push to `main` → Auto-deploys to Vercel ✅

### Backend: Railway Auto-Deploy (No Actions Needed)

1. **Go to Railway Dashboard**
2. **New Project → Deploy from GitHub**
3. **Select your repository**
4. **Configure**:
   - Root Directory: `.` (project root)
   - Build Command: `pip install -r requirements_youtube.txt && python -m spacy download en_core_web_sm`
   - Start Command: `uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables** (Neo4j, API keys, etc.)
6. **Deploy**

**Result**: Every push to `main` → Auto-deploys to Railway ✅

---

## 🚫 Disable Workflows (If Not Needed)

If you're using platform auto-deploy (recommended), you can disable GitHub Actions:

1. **Go to GitHub Repository**
2. **Settings → Actions → General**
3. **Disable workflows** or delete workflow files:
   ```bash
   rm .github/workflows/deploy-frontend.yml
   rm .github/workflows/deploy-backend-railway.yml
   ```

---

## 📋 Current Workflow Status

### ✅ Working (No Secrets Needed)
- `backend-ci.yml` - Tests and lints backend code
- Platform auto-deploy (Vercel/Railway GitHub integration)

### ⚠️ Needs Secrets (Optional)
- `deploy-frontend.yml` - Requires Vercel secrets
- `deploy-backend-railway.yml` - Requires Railway token

---

## 🎯 Quick Fix

**If workflows are failing and you don't need them:**

1. **Use platform auto-deploy instead** (recommended):
   - Vercel: Connect GitHub repo → Auto-deploys
   - Railway: Connect GitHub repo → Auto-deploys

2. **Or disable the workflows**:
   - They're optional - platform auto-deploy is easier

3. **Or set up secrets** (if you want Actions):
   - Follow steps above

---

## 💡 Recommendation

**Use platform auto-deploy** - it's simpler and doesn't require GitHub Actions secrets:
- ✅ Vercel auto-deploys from GitHub
- ✅ Railway auto-deploys from GitHub
- ✅ No secrets to manage
- ✅ Works out of the box

GitHub Actions workflows are **optional** and mainly useful if you want more control over the deployment process.

---

**Status**: Workflows updated to handle missing secrets gracefully. They'll skip deployment if secrets aren't set, rather than failing.

