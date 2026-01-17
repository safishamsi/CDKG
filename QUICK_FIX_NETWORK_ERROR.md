# 🔴 Quick Fix: Network Error

## Problem
George is getting a Network Error when testing the app. This means the backend API is not accessible.

## Solution Steps

### 1. Start Backend Locally
```bash
cd /Users/safi/Downloads/cdkg-challenge-main
python3.9 backend_api_youtube.py
```

**Keep this terminal open** - backend needs to keep running.

### 2. Expose Backend with ngrok
Open a **new terminal** and run:
```bash
ngrok http 8000
```

You'll get a URL like: `https://abc123.ngrok-free.app`

### 3. Update Vercel Environment Variable
1. Go to: https://vercel.com/dashboard
2. Click on your **"cdkg"** project
3. Go to **Settings** → **Environment Variables**
4. Find `VITE_API_URL`
5. Update it to your ngrok URL: `https://abc123.ngrok-free.app`
6. **Save** and **Redeploy**

### 4. Test
- Open your Vercel frontend URL
- Try asking a question
- Should work now!

---

## Alternative: Permanent Backend Hosting

If you want a permanent solution (not ngrok):

### Option A: Render.com (Free tier available)
1. Push backend code to GitHub
2. Connect Render.com to your repo
3. Set root directory to project root (not `frontend`)
4. Set build command: `pip install -r requirements_youtube.txt`
5. Set start command: `uvicorn backend_api_youtube:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (Neo4j, API keys)
7. Update `VITE_API_URL` in Vercel to Render URL

### Option B: Railway.app (Free trial)
Similar to Render - see `DEPLOYMENT_GUIDE.md`

---

## For Monday Meeting

**Before the meeting**:
1. ✅ Start backend + ngrok
2. ✅ Update Vercel env var
3. ✅ Test with QA questions from `QA/CDKGQA.csv`
4. ✅ Have ngrok URL ready to share

**During demo**:
- Show backend running
- Show frontend working
- Test a few QA questions
- Show graph visualization
- Explain YouTube automation pipeline

