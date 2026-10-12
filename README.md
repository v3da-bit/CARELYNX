# CARELYNX — Healthcare Document Intelligence & Clearer Discharge Instructions

> **"Make one part of the patient journey safer, clearer, and easier after discharge."**  
> CARELYNX converts dense, fragmented discharge paperwork into clear, evidence-linked, multilingual care plans while exposing uncertainty and routing ambiguous cases to human review.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.1.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-black.svg?logo=next.js)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg?logo=typescript)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com)
[![AMD ROCm](https://img.shields.io/badge/AMD-ROCm%20vLLM-ED1C24.svg?logo=amd)](https://rocm.docs.amd.com)

---

## 1. The Core Problem & Product Vision

When patients leave the hospital, they typically receive voluminous paperwork: multi-page discharge summaries, handwritten or printed prescriptions, and lab results.

This paperwork is frequently:
- **Long & Fragmented:** Critical instructions are dispersed across multiple pages and documents.
- **Clinically Dense:** Written in medical jargon and abbreviations inaccessible to patients.
- **Inconsistent:** Different documents from the same hospital encounter may state conflicting follow-up dates or instructions.
- **Linguistically Inaccessible:** Rarely provided in the patient's native or preferred language.

### CARELYNX's Solution
CARELYNX acts as an **information-navigation and patient-communication intelligence layer**:
1. **Intakes Documents:** Validates and stores discharge summaries, prescriptions, and lab records.
2. **Page-Aware Processing:** Segments text by page and runs OCR on scanned records with text quality scoring.
3. **Structured Fact Extraction:** Identifies explicit follow-up dates, medications, instructions, and warnings.
4. **Verbatim Evidence Linking:** Every statement links directly to its source document, page, and excerpt snippet.
5. **Conflict & Uncertainty Detection:** If two documents state conflicting dates, the system flags the contradiction and escalates it to human review rather than guessing.
6. **Patient Care Plan:** Displays an intuitive chronological timeline, categorized care instructions, and multilingual toggles (English, Hindi, Gujarati, Marathi, Tamil, Telugu).
7. **Clinical Reviewer Workspace:** Provides staff with a side-by-side document comparator to resolve ambiguities.

---

## 2. Strict Safety Boundaries & Non-Goals

To prevent clinical risk, CARELYNX enforces ironclad safety guardrails:
- ❌ **Zero Autonomous Diagnosis:** Will never interpret symptoms or test results as a medical diagnosis.
- ❌ **Zero Treatment Recommendations:** Will never propose new therapies, medications, or clinical interventions.
- ❌ **Zero Dosage Alterations:** Will never modify, recalculate, or interpret medication dosages.
- ❌ **Zero Hallucinated Fallbacks:** If a document lacks evidence or is invalid, the system refuses to invent facts.
- ❌ **Zero Heuristic Tie-Breaking:** If documents conflict, the system never picks a "winner" automatically; it requires human clinical review.

> **Golden Rule:** If the system cannot support an extracted statement directly from source document evidence, it **must not** present that statement as a verified fact.

---

## 3. High-Level Architecture

```text
                           ┌────────────────────────────┐
                           │      Next.js Frontend      │
                           │   (App Router, TS, Tailwind)│
                           │    Patient & Reviewer UI   │
                           └─────────────┬──────────────┘
                                         │ REST (JSON)
                                         ▼
                           ┌────────────────────────────┐
                           │      FastAPI Backend       │
                           │  (App Factory, Security)   │
                           └─────────────┬──────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
 ┌──────────────┐               ┌──────────────────┐             ┌─────────────────┐
 │ Document API │               │    Cases API     │             │   Reviews API   │
 └──────┬───────┘               └────────┬─────────┘             └────────┬────────┘
        │                                │                                │
        ▼                                ▼                                ▼
 ┌──────────────┐               ┌──────────────────┐             ┌─────────────────┐
 │StorageBackend│               │    SQLAlchemy    │             │   Review Queue  │
 │(Local/Cloud) │               │   Repositories   │             │   & Audit Log   │
 └──────┬───────┘               └────────┬─────────┘             └─────────────────┘
        │                                │
        │               ┌────────────────┴────────────────┐
        │               ▼                                 ▼
        │        SQLite (Local Dev)             PostgreSQL (Docker/Prod)
        │
        ▼
 ┌────────────────────────────────────────────────────────────────────────────────┐
 │                          Document Processing Pipeline                          │
 │                                                                                │
 │   ┌───────────────┐        ┌───────────────────┐       ┌───────────────────┐   │
 │   │  PDF Extractor│───────▶│ OCR Adapter Engine│──────▶│ Text Quality Score│   │
 │   └───────────────┘        └───────────────────┘       └─────────┬─────────┘   │
 │                                                                  │             │
 │                                                                  ▼             │
 │   ┌───────────────┐        ┌───────────────────┐       ┌───────────────────┐   │
 │   │ Safety Engine │◀───────│  Evidence Engine  │◀──────│InferenceProvider  │   │
 │   │(Conflicts/Pol)│        │(Verbatim Matcher) │       │(Rule-Based / ROCm)│   │
 │   └───────┬───────┘        └───────────────────┘       └───────────────────┘   │
 │           │                                                                    │
 │           ▼                                                                    │
 │   ┌───────────────┐        ┌───────────────────┐                               │
 │   │ Care Plan Gen │───────▶│Translation Service│                               │
 │   └───────────────┘        │  (en / hi / gu)   │                               │
 │                            └───────────────────┘                               │
 └────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Team Structure & AI Collaboration

CARELYNX is built by a team of **3 developers** who pair-program with AI assistants:

| Member | Role | Primary Focus | Team Charter |
|---|---|---|---|
| **Member 1** | **Lead Frontend Developer** | `apps/web` (Next.js, Tailwind, React 19, UX polish, accessibility) | [`docs/TEAM.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/TEAM.md) |
| **Member 2** | **Lead Backend Engineer** | `apps/api` (FastAPI, SQLAlchemy, SQLite/Postgres, Storage, Security) | [`docs/TEAM.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/TEAM.md) |
| **Member 3** | **Lead AI & QA Engineer** | `apps/api/app/ai`, Safety, AMD ROCm integration, Evaluation benchmarks | [`docs/TEAM.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/TEAM.md) |

### Guidelines for AI Coding Assistants
Any AI assisting with this repository **must**:
1. Review [`docs/AI_INSTRUCTIONS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_INSTRUCTIONS.md) prior to writing code.
2. Maintain strict fidelity to established project goals without introducing conceptual drift.
3. Append a git-commit formatted log entry to [`docs/AI_LOG.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_LOG.md) upon completing tasks.

---

## 5. Complete Documentation Index (`/docs`)

All architectural specifications, contracts, and guidelines are maintained under [`/docs`](file:///home/common/Documents/Carelynx/CARELYNX/docs):

| Document | Purpose & Description |
|---|---|
| [`docs/PRD.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/PRD.md) | **Product Requirements Document:** Vision, personas, MVP scope, non-goals, and success metrics. |
| [`docs/SRS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/SRS.md) | **Software Requirements Specification:** Functional & non-functional requirements, data validation, and error taxonomy. |
| [`docs/ARCHITECTURE.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/ARCHITECTURE.md) | **System Architecture:** Detailed component breakdown, AMD ROCm vLLM runtime, and database entity relationships. |
| [`docs/TEAM.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/TEAM.md) | **Team Charter:** Member roles (Frontend, Backend, AI/QA), domain ownership, and member instructions. |
| [`docs/AI_INSTRUCTIONS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_INSTRUCTIONS.md) | **AI Pre-Flight Manual:** Mandatory onboarding rules, safety boundaries, and task execution loops for AI coding agents. |
| [`docs/AI_LOG.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_LOG.md) | **AI Task Log:** Git-commit formatted record of all engineering tasks performed by AI assistants. |
| [`docs/API_CONTRACTS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/API_CONTRACTS.md) | **API Contracts:** Complete JSON schemas, headers, error contracts, and endpoints for all routes. |
| [`docs/DATABASE.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/DATABASE.md) | **Database Specification:** PostgreSQL & SQLite schemas, UUID keys, UTC timestamps, and migration commands. |
| [`docs/SAFETY.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/SAFETY.md) | **Safety Guardrails:** Verbatim evidence rules, conflict triggers, OCR handling, and translation constraints. |
| [`docs/DEVELOPMENT_PLAN.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/DEVELOPMENT_PLAN.md) | **Development Roadmap:** Progress tracking across implementation phases (Bootstrap to Demo Hardening). |
| [`docs/IMPLEMENTATION_PLAN.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/IMPLEMENTATION_PLAN.md) | **Implementation Assessment:** Architectural decision records (ADR) and technology evaluation. |

---

## 6. Quickstart & Cross-Platform Setup Guide

CARELYNX runs out-of-the-box on **Windows**, **macOS**, and **Linux** with automated cross-platform runners.

### 6.1 Prerequisites
- **Node.js:** v18+ (v20+ recommended)
- **Python:** 3.10+ (tested with Python 3.12)
- **Git**

### 6.2 1-Command Automated Setup & Run (Recommended)

#### On Any OS (Windows, macOS, Linux):
```bash
# 1. Clone & enter directory
git clone <repo-url>
cd CARELYNX

# 2. Create your local config (never commit .env)
cp .env.example .env          # Windows: copy .env.example .env

# 3. Automated setup (creates venv, installs Python & Node packages, runs DB migrations, generates sample PDFs)
python run.py setup

# 4. Start both backend (FastAPI) and frontend (Next.js) concurrently
python run.py dev
```

#### OS-Specific Shortcuts:
- **Windows (Command Prompt):**
  ```cmd
  run_dev.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  .\run_dev.ps1
  ```
- **macOS / Linux (Bash / Zsh):**
  ```bash
  ./run_dev.sh
  ```

---

### 6.3 Dedicated Service Commands

You can also run individual services independently on any OS:

```bash
python run.py api              # Start FastAPI backend only (http://localhost:8000)
python run.py web              # Start Next.js frontend only (http://localhost:3000)
python run.py test             # Run backend test suite
python run.py generate-samples # Generate sample discharge PDFs
```

---

### 6.4 Manual Step-by-Step Setup

If you prefer running services manually in separate terminals:

#### 0. Configuration
```bash
cp .env.example .env          # Windows: copy .env.example .env
```
Defaults work as-is (SQLite, `rule_based` extraction). Optionally set `GOOGLE_TRANSLATE_API_KEY` for reliable Hindi/Gujarati/Marathi/Tamil/Telugu translation.

#### 1. Backend (FastAPI)
```bash
cd apps/api
# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# Windows:
# python -m venv .venv
# .venv\Scripts\activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend (Next.js)
```bash
cd apps/web
npm install
npm run dev -- -H 0.0.0.0
```

Open your browser to:
- **Patient Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Clinical Reviewer Workspace:** [http://localhost:3000/review](http://localhost:3000/review)
- **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 7. Deployment with Docker (any host)

One `docker-compose.yml` runs the whole stack on any machine with Docker: a laptop, a VM, a cloud server or an AMD GPU box.

```text
browser ──▶ proxy (Caddy :80/:443) ──┬── /api/*  ──▶ api (FastAPI) ──▶ db (Postgres 16)
                                     │                    └──▶ llm (vLLM, optional GPU profile)
                                     └── /*      ──▶ web (Next.js standalone)
```

Only the proxy is published. The web app calls the API at the relative path `/api/v1`, so the same images work on `localhost`, a LAN IP or a domain without rebuilding.

### 7.1 Run it

```bash
cp .env.example .env          # then edit: POSTGRES_PASSWORD (required for anything public), optional keys
docker compose up -d --build  # proxy + web + api + postgres, rule_based extraction (no GPU needed)
```

Open `http://<host>` (or `http://<host>:HTTP_PORT` if you changed `HTTP_PORT`). Database migrations run automatically when the API container starts. Uploaded documents and the database live in the `docstore` and `pgdata` volumes.

| Setting (`.env`) | Purpose |
|---|---|
| `SITE_ADDRESS` | Empty → plain HTTP. A domain (e.g. `carelynx.example.com`) → automatic HTTPS via Let's Encrypt; its DNS must point at the host and ports 80/443 must be open. |
| `HTTP_PORT` / `HTTPS_PORT` | Host ports for the proxy (default 80 / 443). |
| `POSTGRES_PASSWORD` | Change it before exposing the host. |
| `GOOGLE_TRANSLATE_API_KEY` | Reliable Hindi/Gujarati/Marathi/Tamil/Telugu translation (see §6). |
| `REGISTRY` / `TAG` | Image names, for `docker compose build && docker compose push` to your registry; the target host then only needs `docker compose pull && docker compose up -d`. |

### 7.2 Add the LLM (GPU)

The `llm` service is opt-in through a profile. It serves `Qwen/Qwen2.5-7B-Instruct` with vLLM, which needs a GPU with about 24 GB of memory or more.

| Host | Command | `.env` |
|---|---|---|
| AMD GPU (ROCm, Linux, `/dev/kfd` + `/dev/dri`) | `docker compose --profile amd up -d --build` | `INFERENCE_PROVIDER=openai_compat`, `INFERENCE_HARDWARE_LABEL=amd-rocm-vllm` |
| NVIDIA GPU (NVIDIA Container Toolkit) | `docker compose --profile nvidia up -d --build` | `INFERENCE_PROVIDER=openai_compat`, `INFERENCE_HARDWARE_LABEL=nvidia-cuda-vllm` |
| No GPU | `docker compose up -d --build` | leave `INFERENCE_PROVIDER=rule_based` |

- The first start downloads about 15 GB of model weights into the `hf_cache` volume, so the LLM takes a while to become healthy.
- Until then, and whenever the LLM is unreachable, the API falls back to `rule_based` and records that provenance honestly on each fact.
- Benchmark on the GPU host with `python infra/amd/benchmark_rocm.py` (see [`infra/amd/README.md`](infra/amd/README.md)). It labels results "AMD" only when `rocm-smi`/`amd-smi` detect an AMD GPU. **No AMD run has been recorded yet**; the numbers measured so far are the CPU rule-based baseline.
- To run vLLM on a separate GPU machine instead, start it there with `docker compose -f infra/amd/docker-compose.rocm.yml up -d` and set `DOCKER_INFERENCE_BASE_URL=http://<gpu-host>:8080/v1` on the app host.

### 7.3 Operate

```bash
docker compose ps                 # health of every service
docker compose logs -f api        # follow API logs
docker compose up -d --build      # deploy a new version (migrations run on start)
docker compose down               # stop (volumes, i.e. data, are kept)
```

---

## 8. License

Internal Hackathon Project. All rights reserved.
