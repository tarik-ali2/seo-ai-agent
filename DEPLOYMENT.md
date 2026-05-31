# 🚀 SEO AI Agent — Live Deployment Guide

## Architecture
```
Frontend (Next.js)     → Netlify
Backend (FastAPI)      → Railway/Render
Database (SQLite/PG)   → Railway PostgreSQL
```

---

## STEP 1: Backend Deploy (Railway)

### 1.1 Railway Account Banao
1. https://railway.app pe jaao
2. GitHub se login karo (ya email)
3. New Project → GitHub Repository

### 1.2 GitHub pe Push Karo
```bash
cd c:\Users\javed\Downloads\seo-ai-agent
git init
git add .
git commit -m "Initial SEO AI Agent commit"
git remote add origin https://github.com/YOUR_USERNAME/seo-ai-agent.git
git push -u origin main
```

### 1.3 Railway Settings
1. Railway dashboard mein new project create karo
2. GitHub repo select karo
3. **Environment Variables add karo:**
   ```
   ANTHROPIC_API_KEY = sk-proj-xxxxx (console.anthropic.com se)
   SECRET_KEY = very-secret-key-here
   PAGESPEED_API_KEY = (optional, limited requests without it)
   DATABASE_URL = (Railway auto-generates PostgreSQL)
   ```
4. **Deploy** → Automatically deploys whenever push karo
5. **Copy Railway URL** (example: `https://seo-ai-agent-production.up.railway.app`)

---

## STEP 2: Frontend Deploy (Netlify)

### 2.1 Netlify Account Banao
1. https://netlify.com pe login karo (GitHub se)

### 2.2 Update Frontend .env.local
```
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
```

### 2.3 Connect GitHub Repo
1. Netlify dashboard → "New site from Git"
2. GitHub repository select karo
3. **Build Settings:**
   - Build command: `npm run build`
   - Publish directory: `.next`
4. **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL = https://your-railway-url.up.railway.app
   ```
5. **Deploy** ✅

### 2.4 Custom Domain (Optional)
- Netlify → Domain settings → Add custom domain
- CNAME point karo Netlify ko

---

## STEP 3: Test Live

1. Open Netlify URL (example: `https://seo-ai-agent.netlify.app`)
2. Register new account
3. Enter any website URL (bechdu.in, etc.)
4. Run audit ✅

---

## API Keys Kaise Lete Ho

### Anthropic API Key
1. https://console.anthropic.com pe jaao
2. "API Keys" → Create key
3. Railway environment variables mein paste karo

### Google PageSpeed API Key (Optional)
1. https://console.cloud.google.com
2. Enable "PageSpeed Insights API"
3. Create API key → Railway mein add karo

---

## Files Already Ready For Deployment

✅ `backend/Dockerfile` — Backend container config  
✅ `backend/.dockerignore` — Exclude unnecessary files  
✅ `frontend/netlify.toml` — Netlify build config  
✅ `backend/main.py` — Updated with uvicorn runner  

---

## Database Migration (SQLite → PostgreSQL)

Railway auto-provides PostgreSQL. Migration:

```bash
# Local test ke liye SQLite use karo
# Production mein Railway PostgreSQL use hoga automatically
# DATABASE_URL environment variable set karo Railway mein
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **CORS errors** | Backend CORS origins updated for prod URLs |
| **API key invalid** | Check Railway environment variables |
| **Database not found** | Railway auto-creates, wait 2 min after deploy |
| **Build fails** | Check `npm run build` locally first |

---

## Quick Start Commands

```bash
# Locally test production build
cd frontend
npm run build
npm start

# Backend production
cd backend
python main.py  # runs on 8000
```

---

**Ready?** Just say which platform you want for backend (Railway/Render), and I'll guide you step-by-step! 🚀
