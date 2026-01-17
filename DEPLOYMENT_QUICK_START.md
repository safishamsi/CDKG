# 🚀 Quick Deployment Guide

## ✅ What's Deployed on GitHub

### Frontend
- ✅ React/Vite app
- ✅ Auto-deploys to Vercel via GitHub
- ✅ Workflow: `.github/workflows/deploy-frontend.yml`

### Backend
- ✅ FastAPI backend
- ✅ Multiple deployment options
- ✅ Docker support
- ✅ GitHub Actions workflows

---

## 🎯 Quick Start: Deploy Everything

### Step 1: Deploy Backend (Choose One)

#### Option A: Railway (Easiest - Recommended) ⭐

1. **Go to [railway.app](https://railway.app)**
2. **Sign up with GitHub**
3. **New Project** → **Deploy from GitHub repo**
4. **Select**: `safishamsi/CDKG`
5. **Add Environment Variables**:
   ```
   NEO4J_URI=bolt://your-neo4j:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ANTHROPIC_API_KEY=your_key
   YOUTUBE_API_KEY=your_key
   ```
6. **Deploy** → Get URL: `https://your-app.up.railway.app`

**That's it!** Railway auto-deploys on every push to `main`.

#### Option B: Render

1. **Go to [render.com](https://render.com)**
2. **New Web Service** → **GitHub**
3. **Select**: `safishamsi/CDKG`
4. **Settings**:
   - Build: `pip install -r requirements_youtube.txt && python -m spacy download en_core_web_sm`
   - Start: `uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables** (same as Railway)
6. **Deploy** → Get URL: `https://your-app.onrender.com`

#### Option C: Docker

```bash
# Build image
docker build -t cdkg-backend .

# Run container
docker run -p 8000:8000 \
  -e NEO4J_URI="bolt://..." \
  -e NEO4J_USER="neo4j" \
  -e NEO4J_PASSWORD="..." \
  -e ANTHROPIC_API_KEY="..." \
  -e YOUTUBE_API_KEY="..." \
  cdkg-backend
```

---

### Step 2: Deploy Frontend

**Already set up!** Vercel auto-deploys from GitHub.

1. **Check Vercel Dashboard**
   - Go to https://vercel.com/dashboard
   - Your project should be connected to GitHub

2. **Update Environment Variable**
   - Settings → Environment Variables
   - Set `VITE_API_URL` = Your backend URL (from Step 1)
   - Redeploy

3. **Done!** Frontend is live at `https://your-project.vercel.app`

---

## 🔄 Auto-Deployment

### How It Works

1. **Push to GitHub** → Triggers workflows
2. **Backend**: Auto-deploys to Railway/Render (if connected)
3. **Frontend**: Auto-deploys to Vercel (if connected)

### GitHub Actions Workflows

- **`.github/workflows/deploy-frontend.yml`** - Frontend to Vercel
- **`.github/workflows/deploy-backend-railway.yml`** - Backend to Railway
- **`.github/workflows/deploy-backend-render.yml`** - Backend to Render
- **`.github/workflows/backend-ci.yml`** - Backend testing

---

## 📋 Environment Variables Checklist

### Backend (Railway/Render)
- [ ] `NEO4J_URI`
- [ ] `NEO4J_USER`
- [ ] `NEO4J_PASSWORD`
- [ ] `ANTHROPIC_API_KEY`
- [ ] `YOUTUBE_API_KEY`
- [ ] `PORT` (usually auto-set)

### Frontend (Vercel)
- [ ] `VITE_API_URL` (your backend URL)

---

## ✅ Verify Deployment

### Backend Health Check
```bash
curl https://your-backend-url.com/health
```

Should return:
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  ...
}
```

### Frontend
- Open your Vercel URL
- Should load without errors
- Test chatbot functionality

---

## 🔧 Troubleshooting

### Backend Not Deploying
1. Check platform logs
2. Verify environment variables
3. Check GitHub Actions (if using workflows)

### Frontend Can't Connect to Backend
1. Verify `VITE_API_URL` is set correctly
2. Check backend is running
3. Verify CORS settings (backend allows your frontend domain)

### GitHub Actions Failing
1. Check Actions tab for errors
2. Verify secrets are set (Settings → Secrets)
3. Check workflow files for syntax errors

---

## 📚 Full Documentation

- **Backend Deployment**: See `BACKEND_DEPLOYMENT.md`
- **Frontend Deployment**: See `GITHUB_DEPLOYMENT.md`
- **General Deployment**: See `DEPLOYMENT_GUIDE.md`

---

## 🎯 Recommended Setup

1. **Backend**: Railway.app (easiest, free tier)
2. **Frontend**: Vercel (already set up)
3. **Auto-Deploy**: Both connected to GitHub

**Result**: Push to `main` → Everything deploys automatically! 🚀

---

**Status**: ✅ All deployment workflows ready on GitHub!

