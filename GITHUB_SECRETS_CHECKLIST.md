# 🔐 GitHub Secrets Checklist - Quick Reference

## Required Secrets for GitHub Actions Deployment

Go to: **https://github.com/safishamsi/CDKG/settings/secrets/actions**

Click **"New repository secret"** for each:

---

## ✅ Frontend (Vercel) - 3 Secrets Required

### 1. `VERCEL_TOKEN`
- **Get from**: https://vercel.com/account/tokens
- **Steps**:
  1. Click "Create Token"
  2. Name: `github-actions`
  3. Scope: Full Account
  4. Copy token → Add to GitHub

### 2. `VERCEL_ORG_ID`
- **Get from**: https://vercel.com/dashboard
- **Steps**:
  1. Click your team/account name (top right)
  2. Settings → General
  3. Copy "Team ID" → Add to GitHub

### 3. `VERCEL_PROJECT_ID`
- **Get from**: https://vercel.com/dashboard
- **Steps**:
  1. Click your project (cdkg)
  2. Settings → General
  3. Copy "Project ID" → Add to GitHub

---

## ✅ Backend (Railway) - 2 Secrets Required

### 1. `RAILWAY_TOKEN`
- **Get from**: https://railway.app/account/tokens
- **Steps**:
  1. Click "New Token"
  2. Name: `github-actions`
  3. Copy token → Add to GitHub

### 2. `RAILWAY_PROJECT_ID` (NEW - Required)
- **Get from**: Railway dashboard
- **Steps**:
  1. Go to your Railway project
  2. Settings → General
  3. Copy "Project ID" → Add to GitHub

### 3. `RAILWAY_SERVICE` (Optional)
- Service name (default: `backend`)
- Only needed if your service has a different name

---

## ✅ Optional but Recommended

### `VITE_API_URL`
- Your backend URL
- Example: `https://your-backend.railway.app`
- Used during frontend build

---

## 📋 Complete List (Copy-Paste Ready)

Add these secrets in GitHub:

```
VERCEL_TOKEN          → Get from Vercel account tokens
VERCEL_ORG_ID         → Get from Vercel team settings
VERCEL_PROJECT_ID     → Get from Vercel project settings
RAILWAY_TOKEN         → Get from Railway account tokens
RAILWAY_PROJECT_ID    → Get from Railway project settings
RAILWAY_SERVICE       → Optional (default: "backend")
VITE_API_URL          → Optional (your backend URL)
```

---

## 🚀 After Adding Secrets

1. **Push a change** to trigger workflows
2. **Check**: https://github.com/safishamsi/CDKG/actions
3. **Both workflows should succeed** ✅

---

## ❓ How to Get IDs

### Vercel Project ID
1. Go to: https://vercel.com/dashboard
2. Click your project
3. Settings → General
4. Look for "Project ID"

### Vercel Org ID
1. Go to: https://vercel.com/dashboard
2. Click your team name (top right)
3. Settings → General
4. Look for "Team ID"

### Railway Project ID
1. Go to: https://railway.app
2. Click your project
3. Settings → General
4. Look for "Project ID"

---

**That's it!** Once all secrets are added, GitHub Actions will automatically deploy on every push to `main`.

