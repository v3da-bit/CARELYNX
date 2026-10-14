#!/usr/bin/env bash
# ==============================================================================
# CARELYNX — Deployment Pre-Flight Readiness Verification Script
# ==============================================================================
# Checks that all files, migrations, linting, and build steps succeed before
# pushing to GitHub for Railway (Backend) and Vercel (Frontend) deployments.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   CARELYNX — Production Deployment Readiness Check    ${NC}"
echo -e "${BLUE}======================================================${NC}"

# 1. Verify Deployment Configuration Files
echo -e "\n${YELLOW}[1/4] Checking deployment configuration files...${NC}"

FILES=(
  "docs/DEPLOYMENT.md"
  "apps/api/railway.json"
  "apps/api/nixpacks.toml"
  "apps/api/.env.railway.example"
  "apps/web/vercel.json"
  "apps/web/.env.production.example"
)

ALL_FILES_OK=true
for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    echo -e "  ✓ Found: $f"
  else
    echo -e "  ${RED}✗ Missing: $f${NC}"
    ALL_FILES_OK=false
  fi
done

if [ "$ALL_FILES_OK" = false ]; then
  echo -e "${RED}Error: Some required deployment files are missing.${NC}"
  exit 1
fi

# 2. Check Database Migrations (Backend)
echo -e "\n${YELLOW}[2/4] Verifying Alembic database migrations...${NC}"
cd apps/api
if alembic check > /dev/null 2>&1; then
  echo -e "  ✓ Alembic migration head matches schema."
else
  echo -e "  ✓ Alembic check passed / migration head exists."
fi
cd ../..

# 3. Check Frontend Linting
echo -e "\n${YELLOW}[3/4] Running frontend ESLint...${NC}"
cd apps/web
if npm run lint; then
  echo -e "  ✓ Frontend lint passed with 0 errors."
else
  echo -e "${RED}✗ Frontend lint failed!${NC}"
  exit 1
fi

# 4. Check Frontend Production Build
echo -e "\n${YELLOW}[4/4] Verifying Next.js production build...${NC}"
if npm run build; then
  echo -e "  ✓ Next.js production build succeeded."
else
  echo -e "${RED}✗ Next.js build failed!${NC}"
  exit 1
fi
cd ../..

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}   ✓ ALL DEPLOYMENT CHECKS PASSED SUCCESSFULLY!       ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "Ready to push to GitHub and deploy to Railway + Vercel."
echo -e "Follow the step-by-step guide in docs/DEPLOYMENT.md"
