# CARELYNX — Cloudflare Production Deployment Guide

> **Project Name:** CARELYNX  
> **Frontend:** Cloudflare Pages (`carelynx`)  
> **Backend Edge Router:** Cloudflare Workers (`carelynx-api`)  
> **Backend Origin:** FastAPI container on Railway / Docker / Cloudflare Tunnel  

---

## 1. Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           Cloudflare Edge Network                       │
│                                                                         │
│   User Browser ──▶ https://carelynx.pages.dev (Cloudflare Pages)        │
│          │                                                              │
│          ▼ /api/*                                                       │
│   https://carelynx-api.workers.dev (Cloudflare Worker API Gateway)      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Encrypted mTLS / TLS
                                     ▼
                   ┌───────────────────────────────────┐
                   │    FastAPI Application Origin     │
                   │    (Railway / Docker / Cloudflared)│
                   └───────────────────────────────────┘
```

---

## 2. Authentication Requirements

Cloudflare deployments require authentication via either:

1. **Option A: API Token (Recommended for CI/CD & Headless Environments)**
   Export environment variables before deploying:
   ```bash
   export CLOUDFLARE_API_TOKEN="your-cloudflare-api-token"
   export CLOUDFLARE_ACCOUNT_ID="your-cloudflare-account-id"
   ```

2. **Option B: Interactive Browser Login**
   Run the interactive login command:
   ```bash
   npx wrangler login
   ```

---

## 3. Automated One-Command Deployment

Execute the automated deployment script:

```bash
./scripts/deploy_cloudflare.sh
```

This script:
1. Deploys the edge API worker `carelynx-api` to Cloudflare Workers.
2. Builds the Next.js production bundle with Turbopack.
3. Deploys the web client to Cloudflare Pages under the project name `carelynx`.

---

## 4. Manual Deployment Steps

### 4.1 Deploy Backend Edge Gateway (Cloudflare Worker)
```bash
cd apps/api
npx wrangler deploy --name carelynx-api
```

### 4.2 Deploy Frontend (Cloudflare Pages)
```bash
cd apps/web
npm run build
npx wrangler pages deploy .next --project-name carelynx
```
