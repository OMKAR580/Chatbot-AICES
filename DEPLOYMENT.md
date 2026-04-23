# AICES Deployment Guide

AICES is a full-stack application with separate backend (FastAPI) and frontend (React/Vite) services. Deploy them independently for flexibility and scalability.

---

## Frontend Deployment: Vercel

Vercel is the recommended platform for hosting React/Vite applications.

### Steps

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Import Repository to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project" → Select GitHub repo
   - Choose your AICES repository

3. **Configure Build Settings**
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

4. **Add Environment Variables**
   In Vercel project settings, add:
   ```
   VITE_API_BASE_URL=https://your-aices-backend.onrender.com
   VITE_AICES_USER_ID=user_001
   ```

5. **Deploy**
   - Click "Deploy"
   - Vercel auto-deploys on every push to `main`
   - Frontend URL: `https://your-project.vercel.app`

6. **Test**
   ```bash
   curl https://your-project.vercel.app
   ```

---

## Backend Deployment: Render

Render offers a free tier suitable for AICES backend.

### Steps

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Create Web Service on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub repo (AICES)
   - Select repository

3. **Configure Service**
   - **Name:** `aices-backend` (or your choice)
   - **Environment:** `Python 3`
   - **Root Directory:** `/` (leave empty for repo root)
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```

4. **Add Environment Variables**
   In Render dashboard, add:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ALLOWED_ORIGINS=https://your-project.vercel.app
   AICES_DB_PATH=/opt/render/project/src/aices.db
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Render auto-deploys on every push to main branch
   - Backend URL: `https://aices-backend.onrender.com`

6. **Test Health Endpoint**
   ```bash
   curl https://aices-backend.onrender.com/health
   ```

---

## Backend Deployment: Railway

Alternative to Render with similar free tier.

### Steps

1. **Create Railway Project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub"
   - Choose AICES repo

2. **Configure Service**
   - **Root Directory:** `/` (repo root)
   - **Watch Paths:** Leave empty (watch all)

3. **Add Environment Variables**
   In Railway dashboard Variables section:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ALLOWED_ORIGINS=https://your-project.vercel.app
   AICES_DB_PATH=./data/aices.db
   ```

4. **Set Start Command**
   In Railway, set up "start" command:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

5. **Deploy**
   - Railway auto-deploys on GitHub push
   - Get your backend URL from Railway dashboard

6. **Test**
   ```bash
   curl https://your-railway-backend.up.railway.app/health
   ```

---

## Complete Environment Variables Reference

### Backend (.env or platform env vars)
| Variable | Example | Notes |
|----------|---------|-------|
| `OPENAI_API_KEY` | `sk-...` | Required for AI features |
| `OPENAI_MODEL` | `gpt-4o-mini` | Latest recommended model |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` | Comma-separated list |
| `AICES_DB_PATH` | `./data/aices.db` | SQLite file path |
| `DATABASE_URL` | `postgresql://...` | Optional: Use instead of AICES_DB_PATH |

### Frontend (.env.local or Vercel Variables)
| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_BASE_URL` | `https://your-backend.onrender.com` | Backend URL |
| `VITE_AICES_USER_ID` | `user_001` | Demo user (use real auth in production) |

---

## Database: SQLite vs PostgreSQL

### SQLite (Current)
✅ **Pros:**
- No setup required
- File-based, easy backup
- Good for MVP/demo
- Works locally and on free tier

❌ **Cons:**
- Ephemeral on some platforms (resets on redeploy)
- Single user at a time
- Not ideal for production

**Use When:** Demoing, local development, or small-scale usage.

### PostgreSQL (Recommended for Production)
✅ **Pros:**
- Persistent data across deployments
- Multi-user support
- Better performance at scale
- Production-ready

❌ **Cons:**
- Requires paid hosting (e.g., Render, Railway, Vercel Postgres)
- More setup

**Use When:** Production, user data persistence, or team deployment.

#### Switching to PostgreSQL

1. **Create PostgreSQL Database**
   - Render: Add PostgreSQL service in same project
   - Railway: Add PostgreSQL service
   - Vercel: Use Vercel Postgres or external service

2. **Get Connection String**
   - Format: `postgresql+psycopg://user:password@host:5432/aices`

3. **Update Backend Environment**
   ```
   DATABASE_URL=postgresql+psycopg://user:password@host:5432/aices
   ```
   (Remove or leave AICES_DB_PATH unset)

4. **Deploy**
   - Code doesn't change (SQLAlchemy handles the switch)
   - Tables auto-create on first run

---

## Quick Deployment Checklist

- [ ] Repository pushed to GitHub (main branch)
- [ ] `.env` and `.env.local` NOT committed
- [ ] `.gitignore` includes all sensitive/build files
- [ ] Backend and frontend `.env.example` files present
- [ ] OPENAI_API_KEY added to backend environment
- [ ] ALLOWED_ORIGINS set to frontend URL
- [ ] Frontend VITE_API_BASE_URL set to backend URL
- [ ] Health endpoint (`/health`) responds successfully
- [ ] Frontend loads and connects to backend
- [ ] Chat, Quiz, and Progress features work end-to-end

---

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (3.9+)
- Verify dependencies: `pip install -r requirements.txt`
- Check logs on deployment platform

### CORS errors in frontend
- Verify `ALLOWED_ORIGINS` includes frontend URL
- Check backend is accessible: `curl https://your-backend.onrender.com/health`

### OpenAI calls fail
- Verify `OPENAI_API_KEY` is set
- Check API key is valid at [platform.openai.com](https://platform.openai.com/api-keys)
- Ensure account has available credits

### Database not persisting data
- If using SQLite, switch to PostgreSQL for production
- Verify database path is writable and persistent

---

## Support & Resources

- [FastAPI Deployment Docs](https://fastapi.tiangolo.com/deployment/)
- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)
