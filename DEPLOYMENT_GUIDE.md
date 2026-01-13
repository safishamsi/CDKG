# Free Frontend Deployment Guide

This guide shows you how to deploy the frontend for free to show to clients.

## 🚀 Quick Deploy Options

### Option 1: Vercel (Recommended - Easiest)

**Why Vercel?**
- ✅ Free tier (generous limits)
- ✅ Automatic deployments from GitHub
- ✅ Zero configuration needed
- ✅ Fast global CDN
- ✅ Custom domains
- ✅ Perfect for React/Vite apps

**Steps:**

1. **Push your code to GitHub** (if not already):
   ```bash
   cd /Users/safi/Downloads/cdkg-challenge-main
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/cdkg-challenge.git
   git push -u origin main
   ```

2. **Go to [Vercel.com](https://vercel.com)** and sign up (free)

3. **Import your GitHub repository:**
   - Click "Add New Project"
   - Select your repository
   - Vercel will auto-detect Vite settings

4. **Configure environment variables:**
   - In project settings, add:
     ```
     VITE_API_URL=https://your-backend-url.com
     ```
   - If backend is on localhost, you'll need to:
     - Use a service like [ngrok](https://ngrok.com) to expose localhost
     - Or deploy backend separately (see below)

5. **Deploy:**
   - Click "Deploy"
   - Wait ~2 minutes
   - Get your live URL: `https://your-project.vercel.app`

**That's it!** Your frontend is live and will auto-deploy on every git push.

---

### Option 2: Netlify (Also Great)

**Steps:**

1. **Push to GitHub** (same as above)

2. **Go to [Netlify.com](https://netlify.com)** and sign up

3. **Add new site from Git:**
   - Connect GitHub
   - Select repository
   - Build settings (auto-detected):
     - Build command: `cd frontend && npm run build`
     - Publish directory: `frontend/dist`

4. **Add environment variable:**
   - Site settings → Environment variables
   - Add: `VITE_API_URL` = your backend URL

5. **Deploy:**
   - Click "Deploy site"
   - Get URL: `https://your-project.netlify.app`

---

### Option 3: Cloudflare Pages (Fast & Free)

**Steps:**

1. **Push to GitHub**

2. **Go to [Cloudflare Pages](https://pages.cloudflare.com)**

3. **Connect repository**

4. **Build settings:**
   - Framework preset: Vite
   - Build command: `cd frontend && npm run build`
   - Build output directory: `frontend/dist`

5. **Add environment variable:**
   - `VITE_API_URL` = your backend URL

6. **Deploy**

---

## 🔧 Backend Options

Your frontend needs to connect to the backend API. Options:

### Option A: Keep Backend Local + Use ngrok

1. **Run backend locally:**
   ```bash
   python backend_api_youtube.py
   ```

2. **Install ngrok:**
   ```bash
   brew install ngrok  # macOS
   # or download from ngrok.com
   ```

3. **Expose localhost:**
   ```bash
   ngrok http 8000
   ```
   - Get public URL: `https://abc123.ngrok.io`
   - Use this as `VITE_API_URL` in frontend deployment

**Note:** Free ngrok URLs change on restart. For demos, this is fine.

### Option B: Deploy Backend to Render/Railway

**Render (Free tier):**
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Settings:
   - Build command: `pip install -r requirements_youtube.txt`
   - Start command: `python backend_api_youtube.py`
   - Add environment variables (Neo4j, API keys, etc.)
5. Get URL: `https://your-backend.onrender.com`

**Railway (Free tier):**
- Similar process, very easy setup

### Option C: Use Existing Backend URL

If you already have a backend deployed, just use that URL.

---

## 📝 Pre-Deployment Checklist

1. **Test build locally:**
   ```bash
   cd frontend
   npm run build
   npm run preview  # Test the build
   ```

2. **Set API URL:**
   - Make sure `VITE_API_URL` is set correctly
   - Test with: `VITE_API_URL=https://your-backend.com npm run dev`

3. **Check CORS:**
   - Backend should allow your frontend domain
   - Check `backend_api_youtube.py` CORS settings:
     ```python
     allow_origins=["http://localhost:3000", "http://localhost:5173", "https://your-frontend.vercel.app"]
     ```

4. **Environment Variables:**
   - Frontend: `VITE_API_URL`
   - Backend: All your existing env vars (Neo4j, API keys, etc.)

---

## 🎯 Quick Start (Vercel - 5 minutes)

```bash
# 1. Install Vercel CLI (optional, but helpful)
npm i -g vercel

# 2. In your project root
cd frontend
vercel

# 3. Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? cdkg-chatbot (or your choice)
# - Directory? ./frontend
# - Override settings? No

# 4. Add environment variable
vercel env add VITE_API_URL
# Enter your backend URL when prompted

# 5. Redeploy
vercel --prod
```

**Done!** You'll get a URL like: `https://cdkg-chatbot.vercel.app`

---

## 🔒 Security Notes

1. **Don't commit API keys** - Use environment variables
2. **CORS** - Only allow your frontend domain
3. **Rate limiting** - Consider adding to backend for production
4. **HTTPS** - All free hosts provide HTTPS automatically

---

## 📊 Comparison

| Service | Free Tier | Ease | Speed | Best For |
|---------|-----------|------|-------|----------|
| **Vercel** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | React/Vite apps |
| **Netlify** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Static sites |
| **Cloudflare Pages** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Fast global CDN |
| **GitHub Pages** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Simple sites |

**Recommendation:** Use **Vercel** - it's the easiest and best for Vite/React apps.

---

## 🐛 Troubleshooting

**Build fails:**
- Check Node version (Vercel uses Node 18+)
- Check `package.json` scripts
- Check for missing dependencies

**API calls fail:**
- Check CORS settings in backend
- Verify `VITE_API_URL` is set correctly
- Check browser console for errors
- Test backend URL directly

**Environment variables not working:**
- Make sure they start with `VITE_` for Vite
- Redeploy after adding env vars
- Check variable names match exactly

---

## 🎉 After Deployment

1. **Share the URL** with your client
2. **Test all features:**
   - Chat functionality
   - Graph visualization
   - Search features
3. **Monitor:**
   - Vercel dashboard shows analytics
   - Check error logs if issues occur

---

## 💡 Pro Tips

1. **Custom Domain (Free):**
   - Vercel/Netlify allow custom domains on free tier
   - Looks more professional: `demo.yourcompany.com`

2. **Preview Deployments:**
   - Every PR gets a preview URL
   - Test before merging to main

3. **Analytics:**
   - Vercel provides basic analytics for free
   - See page views, performance metrics

4. **Backend on Same Service:**
   - Render/Railway can host both frontend and backend
   - Easier to manage, but may be slower

---

## 📞 Need Help?

- **Vercel Docs:** https://vercel.com/docs
- **Netlify Docs:** https://docs.netlify.com
- **Vite Deployment:** https://vitejs.dev/guide/static-deploy.html

Good luck with your client demo! 🚀

