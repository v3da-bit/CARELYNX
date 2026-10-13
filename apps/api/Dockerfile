FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Tesseract binary for image OCR (the Python bindings come from requirements.txt).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Mirror the repo layout: app/core/config.py derives REPO_ROOT as two levels above apps/api.
WORKDIR /opt/carelynx/apps/api
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN useradd --system --uid 10001 carelynx \
    && mkdir -p /data/storage \
    && chown -R carelynx /data /opt/carelynx
USER carelynx

EXPOSE 8000
# --proxy-headers: client IP/scheme come from the Caddy proxy. Workers: set WEB_CONCURRENCY (uvicorn reads it).
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'"]
