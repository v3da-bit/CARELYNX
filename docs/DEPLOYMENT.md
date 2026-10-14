# CARELYNX — Production Deployment Guide

> **Stack:** Next.js 16 (Vercel) + FastAPI (Railway) + PostgreSQL (Railway Plugin)  
> **Estimated time:** 20–30 minutes  
> **Cost:** Free tier for both platforms — no credit card required for basic usage.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                  PRODUCTION TOPOLOGY                     │
│                                                          │
│  Browser ──► Vercel CDN (Next.js)                        │
│                    │                                     │
│              /api/v1/* rewrite                           │
│                    │                                     │
│              Railway (FastAPI) ──► Railway PostgreSQL    │
│                    │                                     │
│                 Gemini API (inference)                   │
└──────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before starting, make sure you have:

- [ ] **GitHub account** — code must be in the `v3da-bit/CARELYNX` repo (already done)
- [ ] **Vercel account** — sign up free at [vercel.com](https://vercel.com) (GitHub login recommended)
- [ ] **Railway account** — sign up free at [railway.app](https://railway.app) (GitHub login recommended)
- [ ] **Gemini API Key** — from [aistudio.google.com](https://aistudio.google.com)
- [ ] Git is installed locally

---

## Part 1 — Deploy the Backend to Railway

### Step 1.1 — Create a new Railway project

1. Log in to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Choose **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select the **`v3da-bit/CARELYNX`** repository

### Step 1.2 — Configure the root directory

Railway will detect the repo root by default. You need to point it at the API subfolder:

1. Once the project is created, click on the **service card**
2. Go to **Settings** tab
3. Under **Source**, set **Root Directory** to:
   ```
   apps/api
   ```
4. Railway will auto-detect `nixpacks.toml` and `railway.json` from that directory

### Step 1.3 — Add a PostgreSQL database

1. In your Railway project view, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway creates a Postgres instance and **automatically injects** `DATABASE_URL` into your service environment
3. Click on the PostgreSQL service → **"Connect"** tab → copy the **connection string** for reference

> **Important:** The `DATABASE_URL` injected by Railway uses the `postgresql://` scheme. CARELYNX requires `postgresql+psycopg://` for psycopg3 compatibility. You will override this in Step 1.4.

### Step 1.4 — Set environment variables

1. Click on your **FastAPI service** → **"Variables"** tab
2. Click **"Raw Editor"** and paste the contents below (replace all placeholder values):

```bash
ENVIRONMENT=production
DEBUG=false

# From Railway Postgres plugin Variables tab → copy DATABASE_PUBLIC_URL
# Change "postgresql://" to "postgresql+psycopg://"
DATABASE_URL=postgresql+psycopg://USER:PASS@HOST.railway.internal:5432/railway

# Your Vercel URL — you will know this after Part 2 (come back to update it)
CORS_ORIGINS=https://YOUR_APP_NAME.vercel.app

STORAGE_BACKEND=local
STORAGE_LOCAL_DIR=/data/storage
MAX_UPLOAD_MB=10

# Generate a strong key: python -c "import secrets; print(secrets.token_hex(32))"
AUTH_SECRET_KEY=REPLACE_WITH_64_CHAR_HEX_SECRET

INFERENCE_PROVIDER=openai_compat
INFERENCE_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
INFERENCE_MODEL=gemini-1.5-flash
INFERENCE_API_KEY=YOUR_GEMINI_API_KEY_HERE
INFERENCE_TIMEOUT_S=60
INFERENCE_HARDWARE_LABEL=gemini-cloud

GOOGLE_TRANSLATE_API_KEY=
SAFETY_MIN_PAGE_QUALITY=0.85
SAFETY_MIN_FACT_CONFIDENCE=0.80
```

3. Click **"Update Variables"**. Railway will redeploy automatically.

### Step 1.5 — Get the DATABASE_URL from the Postgres plugin

1. Click the **PostgreSQL service** in Railway
2. Go to the **"Variables"** tab
3. Find `DATABASE_URL` — it looks like:
   ```
   postgresql://postgres:PASSWORD@monorail.proxy.rlwy.net:PORT/railway
   ```
4. Copy it, change `postgresql://` to `postgresql+psycopg://`
5. Paste into your FastAPI service Variables → `DATABASE_URL`

### Step 1.6 — Verify the backend is running

1. Click on the **FastAPI service** → **"Deployments"** tab
2. Wait for the build to complete (2–4 minutes)
3. Click **"View Logs"** — you should see:
   ```
   INFO  [alembic.runtime.migration] Running upgrade -> 0001, Initial schema
   INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, Add users and cases.user_id
   INFO:     Application startup complete.
   ```
4. Click **Settings** → **Networking** → **Generate Domain**
5. Copy your Railway URL: `https://YOUR_SERVICE.railway.app`
6. Test the health endpoint:
   ```
   https://YOUR_SERVICE.railway.app/api/v1/health
   ```
   Expected response: `{"status": "ok", ...}`

> **Save this URL** — you need it for Part 2.

---

## Part 2 — Deploy the Frontend to Vercel

### Step 2.1 — Import project on Vercel

1. Log in to [vercel.com](https://vercel.com)
2. Click **"Add New"** → **"Project"**
3. Click **"Import Git Repository"**
4. Select **`v3da-bit/CARELYNX`**
5. Click **"Import"**

### Step 2.2 — Configure project settings

On the configuration screen:

| Setting | Value |
|---|---|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `apps/web` |
| **Build Command** | `next build` (default) |
| **Output Directory** | `.next` (default) |
| **Install Command** | `npm ci` (default) |

> **Critical:** Set **Root Directory** to `apps/web` — Vercel will scan your monorepo and deploy only the frontend.

### Step 2.3 — Set environment variables

Still on the configuration screen, expand **"Environment Variables"** and add:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://YOUR_SERVICE.railway.app/api/v1` |

Replace `YOUR_SERVICE` with the Railway URL from Step 1.6.

### Step 2.4 — Deploy

1. Click **"Deploy"**
2. Wait for the build to complete (1–3 minutes)
3. Vercel gives you a URL: `https://carelynx-xyz.vercel.app`

### Step 2.5 — Update CORS on Railway

Now that you have the Vercel URL, go back to Railway:

1. FastAPI service → **"Variables"** tab
2. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://carelynx-xyz.vercel.app
   ```
3. Railway auto-redeploys.

### Step 2.6 — Test the full app

Open your Vercel URL in the browser. You should see the CARELYNX dashboard. Try:
- Uploading a PDF discharge summary
- Viewing extracted medical facts
- Translating a case

---

## Part 3 — Update vercel.json (Optional API Proxy)

The included `apps/web/vercel.json` has an optional rewrite rule that proxies `/api/v1/*` through Vercel to Railway (avoids CORS issues completely):

1. Edit `apps/web/vercel.json` — replace `YOUR_RAILWAY_BACKEND_URL` with your actual Railway domain
2. Change `NEXT_PUBLIC_API_BASE_URL` in Vercel to `/api/v1` (relative, no domain)
3. Push to GitHub — Vercel auto-redeploys

If you prefer direct calls (simpler, keep CORS config): leave `NEXT_PUBLIC_API_BASE_URL` pointing to the full Railway URL and ignore the rewrites block.

---

## Part 4 — Custom Domain (Optional)

### Vercel custom domain
1. Vercel → Project → **Settings** → **Domains**
2. Add your domain → follow DNS instructions (CNAME record)

### Railway custom domain
1. Railway → Service → **Settings** → **Networking** → **Custom Domain**
2. Add domain → follow DNS instructions

---

## Environment Variables Quick Reference

### Railway (Backend) Variables

| Variable | Required | Example Value |
|---|---|---|
| `ENVIRONMENT` | Yes | `production` |
| `DATABASE_URL` | Yes | `postgresql+psycopg://user:pass@host:5432/db` |
| `CORS_ORIGINS` | Yes | `https://your-app.vercel.app` |
| `AUTH_SECRET_KEY` | Yes | 64-char hex string |
| `INFERENCE_PROVIDER` | Yes | `openai_compat` |
| `INFERENCE_BASE_URL` | Yes | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `INFERENCE_MODEL` | Yes | `gemini-1.5-flash` |
| `INFERENCE_API_KEY` | Yes | Your Gemini API key |
| `STORAGE_LOCAL_DIR` | Yes | `/data/storage` |
| `GOOGLE_TRANSLATE_API_KEY` | No | Optional for translation |

### Vercel (Frontend) Variables

| Variable | Required | Example Value |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `https://your-service.railway.app/api/v1` |

---

## Troubleshooting

### Build fails on Railway: `ModuleNotFoundError`
- Check the Logs tab — copy the exact error
- Ensure all dependencies are in `apps/api/requirements.txt`
- Confirm **Root Directory** is set to `apps/api` in Railway Settings

### `DATABASE_URL` connection error
- Verify you changed `postgresql://` to `postgresql+psycopg://`
- Use the internal URL (`*.railway.internal`) for same-project services, not the public proxy URL

### CORS error in browser console
- Confirm `CORS_ORIGINS` on Railway exactly matches your Vercel domain (no trailing slash)
- After updating `CORS_ORIGINS`, wait for Railway to redeploy (~1 min)

### Alembic migration fails
- Check Railway logs for the migration error
- If `table already exists`, check that migrations have proper `IF NOT EXISTS` guards

### Vercel build fails: TypeScript errors
- Run `npm run build` locally in `apps/web` to reproduce and fix before pushing

### PDF uploads not persisting (Railway ephemeral filesystem)
- Railway's filesystem resets between deploys
- For production persistence, a future task should implement `storage_backend=s3` (Cloudflare R2 or AWS S3) — see `task_backlog.json`

---

## Deployment Files Reference

| File | Purpose |
|---|---|
| `apps/api/railway.json` | Railway service config — start command, restart policy |
| `apps/api/nixpacks.toml` | Nixpacks build — installs Python 3.13 + Tesseract OCR |
| `apps/web/vercel.json` | Vercel config — framework, security headers, optional API proxy |
| `apps/api/.env.railway.example` | Railway env variable template (copy values into Railway dashboard) |
| `apps/web/.env.production.example` | Vercel env variable template |
| `docs/DEPLOYMENT.md` | This guide |

---

## Push Deployment Files to GitHub

```bash
cd /Users/vedantkhamar/Desktop/Drive_D/CARELYNX

git add apps/api/railway.json \
        apps/api/nixpacks.toml \
        apps/api/.env.railway.example \
        apps/web/vercel.json \
        apps/web/.env.production.example \
        docs/DEPLOYMENT.md

git commit -m "deploy: add Railway + Vercel deployment configuration and guide"

git push origin main
```

---

*Last updated by Antigravity AI — 2026-10-14*
