# CARELYNX — Agent-Ready Project Specification

## What is this?

This directory contains the engineering specification for CARELYNX, an AMD ACT 3 hackathon MVP.

Primary focus:

> **Clearer discharge instructions**

The package is designed to be provided directly to Claude Code or another coding agent.

## Start here

The agent must read:

```text
CLAUDE.md
docs/PRD.md
docs/SRS.md
docs/ARCHITECTURE.md
docs/SAFETY.md
docs/API_CONTRACTS.md
docs/DATABASE.md
docs/DEVELOPMENT_PLAN.md
task_backlog.json
state.json
```

Then execute `CLX-000`.

## Product

CARELYNX transforms complex discharge documents into:

- evidence-linked information
- clear care plans
- documented follow-ups
- multilingual communication
- uncertainty alerts
- human-review cases

It must never become an autonomous diagnosis/treatment system.

## MVP demo

The final demo must show:

1. Normal document processing.
2. Evidence-linked care plan.
3. Hindi/Gujarati translation.
4. Bad OCR → review.
5. Conflicting documents → review.
6. Human resolution.
7. Measured impact.
8. AMD-powered AI inference.

## Development principle

Build a reliable narrow workflow first. Do not expand into an EHR, diagnostic engine, pharmacy platform or autonomous clinical system.

## Setup & Run Instructions

### 1. Environment Variables
Copy the template to create your `.env` file:
```bash
cp .env.example .env
```

### 2. Backend (FastAPI)
The API runs on Python 3.10+ and uses SQLite by default (no Docker needed for local dev).
```bash
cd apps/api
python -m venv .venv

# On Mac/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

pip install -r requirements.txt

# Create the database tables
alembic upgrade head

# Start the API server on http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend (Next.js)
The frontend uses Next.js and Tailwind CSS.
```bash
cd apps/web
npm install

# Start the dev server on http://localhost:3000
npm run dev -- -H 0.0.0.0
```

### 4. Running the Demo
Once both servers are running:
1. Open `http://localhost:3000` in your browser.
2. The system defaults to a fast `rule_based` regex AI provider for local testing without GPUs.
3. You can upload standard medical PDFs (like the included `sample_medical_record.pdf`) to test the end-to-end extraction and review pipeline.
