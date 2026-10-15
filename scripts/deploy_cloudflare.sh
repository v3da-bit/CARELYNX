#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# CARELYNX — Automated Cloudflare Deployment Script
# ==============================================================================

echo "=================================================================="
echo " CARELYNX — Cloudflare Production Deployment"
echo "=================================================================="

# Check for Cloudflare authentication
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "Checking Wrangler interactive login status..."
  if ! npx -y wrangler whoami >/dev/null 2>&1; then
    echo "⚠️  Wrangler is not authenticated."
    echo "Please set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID, or run:"
    echo "  npx wrangler login"
    exit 1
  fi
fi

# 1. Deploy Backend API Worker to Cloudflare
echo "Step 1: Deploying Backend Edge Worker (carelynx-api)..."
cd apps/api
npx -y wrangler deploy --name carelynx-api
cd ../..

# 2. Build and Deploy Frontend to Cloudflare Pages
echo "Step 2: Building Next.js Frontend for Cloudflare Pages..."
cd apps/web
npm run build
echo "Deploying to Cloudflare Pages (carelynx)..."
npx -y wrangler pages deploy .next --project-name carelynx --commit-dirty=true
cd ../..

echo "=================================================================="
echo "✅ CARELYNX successfully deployed to Cloudflare!"
echo "=================================================================="
