# Backend Deployment Guide

This guide covers deploying the backend API to various platforms via GitHub.

---

## 🚀 Quick Deploy Options

### Option 1: Railway.app (Recommended - Easiest) ⭐

**Why Railway?**
- ✅ Free tier with $5 credit/month
- ✅ Auto-detects Python
- ✅ Simple GitHub integration
- ✅ Better for ML/AI apps
- ✅ Automatic deployments from GitHub

**Steps:**

1. **Go to [railway.app](https://railway.app)**
   - Sign up with GitHub
   - Authorize Railway to access your repositories

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select `safishamsi/CDKG`

3. **Configure Service**
   - Railway auto-detects Python
   - Uses `railway.json` for configuration
   - Build command: `pip install -r requirements_youtube.txt && python -m spacy download en_core_web_sm`
   - Start command: `uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - Go to Variables tab
   - Add:
     ```
     NEO4J_URI=bolt://your-neo4j-instance:7687
     NEO4J_USER=neo4j
     NEO4J_PASSWORD=your_password
     ANTHROPIC_API_KEY=your_key
     YOUTUBE_API_KEY=your_key
     PORT=8000
     ```

5. **Deploy**
   - Railway automatically deploys on push to `main`
   - Get URL: `https://your-app.up.railway.app`

6. **GitHub Actions (Optional)**
   - Add secret: `RAILWAY_TOKEN` (get from Railway → Settings → Tokens)
   - Workflow: `.github/workflows/deploy-backend-railway.yml`
   - Auto-deploys on code changes

---

### Option 2: Render.com (Free Tier Available)

**Steps:**

1. **Go to [render.com](https://render.com)**
   - Sign up with GitHub
   - Connect your repository

2. **Create New Web Service**
   - Select `safishamsi/CDKG` repository
   - Settings:
     - **Name**: `cdkg-backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements_youtube.txt && python -m spacy download en_core_web_sm`
     - **Start Command**: `uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT`
     - **Root Directory**: `.` (project root)

3. **Add Environment Variables**
   - Same as Railway (see above)

4. **Deploy**
   - Render auto-deploys on push to `main`
   - Get URL: `https://cdkg-backend.onrender.com`

5. **GitHub Actions (Optional)**
   - Add secrets:
     - `RENDER_API_KEY` (get from Render → Account Settings → API Keys)
     - `RENDER_SERVICE_ID` (get from your service URL)
   - Workflow: `.github/workflows/deploy-backend-render.yml`

**Note**: Free tier instances spin down after inactivity. First request may be slow.

---

### Option 3: Fly.io (Good for Python Apps)

**Steps:**

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign Up**
   ```bash
   fly auth signup
   ```

3. **Launch App**
   ```bash
   fly launch
   ```
   - Follow prompts
   - Creates `fly.toml` (if not exists)

4. **Set Secrets**
   ```bash
   fly secrets set NEO4J_URI="bolt://..." NEO4J_USER="neo4j" NEO4J_PASSWORD="..." ANTHROPIC_API_KEY="..." YOUTUBE_API_KEY="..."
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Get URL**
   ```bash
   fly info
   ```

---

### Option 4: DigitalOcean App Platform

**Steps:**

1. **Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)**
   - Sign up
   - Create App → GitHub

2. **Configure**
   - Select repository
   - Build command: `pip install -r requirements_youtube.txt && python -m spacy download en_core_web_sm`
   - Run command: `uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT`
   - Add environment variables

3. **Deploy**
   - Auto-deploys on push

**Pricing**: Starts at $5/month

---

## 🔧 GitHub Actions Workflows

### Available Workflows

1. **`.github/workflows/deploy-backend-railway.yml`**
   - Deploys to Railway on push to `main`
   - Requires: `RAILWAY_TOKEN` secret

2. **`.github/workflows/deploy-backend-render.yml`**
   - Triggers Render deployment
   - Requires: `RENDER_API_KEY` and `RENDER_SERVICE_ID` secrets

3. **`.github/workflows/backend-ci.yml`**
   - Tests and lints backend code
   - Runs on push and pull requests

### Setting Up Secrets

1. **Go to GitHub Repository**
   - Settings → Secrets and variables → Actions

2. **Add Secrets**:

   **For Railway:**
   - `RAILWAY_TOKEN` - Get from Railway → Settings → Tokens

   **For Render:**
   - `RENDER_API_KEY` - Get from Render → Account Settings → API Keys
   - `RENDER_SERVICE_ID` - Extract from your Render service URL

3. **Workflows will use these automatically**

---

## 📋 Environment Variables Required

All platforms need these environment variables:

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687  # or your Neo4j instance
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
YOUTUBE_API_KEY=your_youtube_key

# Server
PORT=8000  # Usually set automatically by platform
```

---

## 🚀 Deployment Files

The repository includes these deployment configuration files:

- **`Procfile`** - For Heroku/Render
  ```
  web: uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT
  ```

- **`railway.json`** - For Railway
  ```json
  {
    "build": {
      "builder": "NIXPACKS",
      "buildCommand": "pip install -r requirements_youtube.txt && python -m spacy download en_core_web_sm"
    },
    "deploy": {
      "startCommand": "uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT",
      "healthcheckPath": "/health",
      "healthcheckTimeout": 100
    }
  }
  ```

- **`runtime.txt`** - Python version
  ```
  python-3.9.18
  ```

---

## ✅ Post-Deployment Checklist

1. **Verify Health Endpoint**
   ```bash
   curl https://your-backend-url.com/health
   ```
   Should return: `{"status": "healthy", ...}`

2. **Test API Endpoint**
   ```bash
   curl https://your-backend-url.com/api/query \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
   ```

3. **Update Frontend**
   - Update `VITE_API_URL` in Vercel to your backend URL
   - Redeploy frontend

4. **Monitor Logs**
   - Check platform logs for errors
   - Verify Neo4j connection
   - Check API key validity

---

## 🔄 Auto-Deployment Setup

### Railway (Recommended)

1. **Connect GitHub** in Railway dashboard
2. **Enable Auto-Deploy** (enabled by default)
3. **Push to `main`** → Auto-deploys

### Render

1. **Connect GitHub** in Render dashboard
2. **Auto-Deploy** enabled by default
3. **Push to `main`** → Auto-deploys

### GitHub Actions

1. **Add secrets** (see above)
2. **Workflows run automatically** on push
3. **Check Actions tab** for deployment status

---

## 🐛 Troubleshooting

### Backend Won't Start

1. **Check logs** in platform dashboard
2. **Verify environment variables** are set
3. **Check Python version** (should be 3.9+)
4. **Verify dependencies** installed correctly

### Neo4j Connection Failed

1. **Check NEO4J_URI** format: `bolt://host:7687`
2. **Verify credentials** are correct
3. **Check firewall** - Neo4j instance must be accessible
4. **For Aura**: Use `neo4j+s://` protocol

### API Keys Not Working

1. **Verify keys** are set correctly
2. **Check key permissions** (YouTube API quota, etc.)
3. **Test keys locally** first

### Deployment Fails

1. **Check GitHub Actions logs**
2. **Verify secrets** are set correctly
3. **Check platform-specific logs**

---

## 📊 Platform Comparison

| Platform | Free Tier | Auto-Deploy | Ease of Setup | Best For |
|----------|-----------|-------------|---------------|----------|
| **Railway** | ✅ $5/month credit | ✅ Yes | ⭐⭐⭐⭐⭐ | Quick demos |
| **Render** | ✅ Limited | ✅ Yes | ⭐⭐⭐⭐ | Production |
| **Fly.io** | ✅ Limited | ⚠️ Manual | ⭐⭐⭐ | Global scale |
| **DigitalOcean** | ❌ Paid | ✅ Yes | ⭐⭐⭐ | Production |

---

## 🎯 Recommendation

**For Quick Demo**: Use **Railway.app**
- Easiest setup
- Free tier
- Auto-deploys from GitHub
- Works great for demos

**For Production**: Use **Render.com** or **DigitalOcean**
- More reliable
- Better uptime
- Production-ready

---

## 📝 Next Steps

1. **Choose a platform** (Railway recommended)
2. **Deploy backend** following steps above
3. **Get backend URL**
4. **Update frontend** `VITE_API_URL` in Vercel
5. **Test end-to-end**

---

**Status**: ✅ Backend deployment workflows ready!

