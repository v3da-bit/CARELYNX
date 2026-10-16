# CARELYNX — Healthcare Document Intelligence & Clearer Discharge Instructions

> **"Make one part of the patient journey safer, clearer, and easier after discharge."**  
> CARELYNX converts dense, fragmented discharge paperwork into clear, evidence-linked, patient-friendly care plans while exposing clinical uncertainty and routing ambiguous cases to human clinical review.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.142.2-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3.8-black.svg?logo=next.js)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19.2.8-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg?logo=typescript)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS%20v4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.1.3-D71F00.svg)](https://www.sqlalchemy.org)
[![AMD ROCm](https://img.shields.io/badge/AMD-ROCm%20vLLM-ED1C24.svg?logo=amd)](https://rocm.docs.amd.com)

---

## 1. The Core Problem & Product Vision

When leaving a hospital, patients routinely receive thick packets of discharge paperwork: multi-page hospital summaries, printed or handwritten prescription slips, laboratory diagnostic sheets, and follow-up consultation notes.

This paperwork is frequently:
- **Fragmented & Disorganized:** Vital recovery instructions and warnings are scattered across multiple disparate pages and documents.
- **Clinically Dense:** Packed with medical jargon, abbreviations, and clinical shorthand that patients and family caregivers struggle to interpret.
- **Inconsistent & Conflicting:** Different papers from the same hospital admission frequently state contradictory medication dosages, instructions, or follow-up appointment dates.
- **Linguistically Inaccessible:** Almost exclusively issued in English or clinical medical terminology, creating severe safety risks for non-English speakers.

### How CARELYNX Solves This
CARELYNX operates as an **evidence-linked clinical intelligence and patient communication layer**:
1. **Multi-Format Ingestion:** Ingests discharge summaries, prescriptions, and lab records (PDF, PNG, JPEG) with strict magic-byte validation and secure local storage.
2. **Page-Aware Processing & OCR:** Extracts text page-by-page, running high-accuracy OCR on scanned or photographic records alongside automated text quality scoring.
3. **Structured Clinical Extraction:** Identifies explicit follow-up dates, scheduled appointments, prescribed medications, home-care instructions, and red-flag warning signs.
4. **Verbatim Evidence Linking:** Every single extracted fact links directly to its source document, page number, and exact text snippet.
5. **Conflict & Uncertainty Detection:** If two documents state conflicting dates or dosages, CARELYNX flags the contradiction immediately and escalates it to a human clinician rather than guessing.
6. **Patient Care Plan:** Visualizes an intuitive chronological timeline, structured recovery checklist, and one-click multilingual toggles (English, Hindi, Gujarati, Marathi, Tamil, Telugu).
7. **Clinical Reviewer Workspace:** Equips medical staff with an interactive side-by-side document comparator to review, verify, edit, or reject flagged ambiguities.

---

## 2. Strict Safety Boundaries & Non-Goals

To prevent patient harm and clinical risk, CARELYNX enforces ironclad safety guardrails:

- ❌ **Zero Autonomous Diagnosis:** Never infers, guesses, or suggests clinical conditions or medical diagnoses from symptoms or lab values.
- ❌ **Zero Treatment Recommendations:** Never suggests new medications, alternative therapies, or unprescribed clinical interventions.
- ❌ **Zero Dosage Alterations:** Never recalculates, rounds, or alters medication dosages or frequencies.
- ❌ **Zero Hallucinated Fallbacks:** If a record lacks clear evidence or cannot be verified, the system refuses to extrapolate fake medical details.
- ❌ **Zero Heuristic Tie-Breaking:** If two documents state conflicting instructions, the system never arbitrarily picks a "winner"; it escalates the conflict directly to human clinical review.

> **Golden Safety Rule:** If the system cannot support an extracted statement directly from verbatim source document evidence, it **must never** present that statement as a verified fact.

---

## 3. System Architecture

```text
                            ┌────────────────────────────────────┐
                            │          Next.js Frontend          │
                            │      (App Router, React 19)        │
                            │  Patient & Clinical Reviewer UI    │
                            └─────────────────┬──────────────────┘
                                              │ REST (JSON)
                                              ▼
                            ┌────────────────────────────────────┐
                            │          FastAPI Backend           │
                            │     (Python 3.10+, Security)       │
                            └─────────────────┬──────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
  ┌──────────────┐                     ┌──────────────┐                     ┌──────────────┐
  │ Document API │                     │  Cases API   │                     │ Reviews API  │
  └──────┬───────┘                     └──────┬───────┘                     └──────┬───────┘
         │                                    │                                    │
         ▼                                    ▼                                    ▼
  ┌──────────────┐                     ┌──────────────┐                     ┌──────────────┐
  │PrivateStore  │                     │  SQLAlchemy  │                     │ Review Queue │
  │(Local / S3)  │                     │ Repositories │                     │ & Audit Log  │
  └──────┬───────┘                     └──────┬───────┘                     └──────────────┘
         │                                    │
         │                     ┌──────────────┴──────────────┐
         │                     ▼                             ▼
         │              SQLite (Local)             PostgreSQL (Production)
         ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                              Document Processing Pipeline                              │
  │                                                                                        │
  │   ┌───────────────┐        ┌───────────────────┐        ┌──────────────────────────┐   │
  │   │ PDF Extractor │───────▶│ OCR Adapter Engine│───────▶│   Text Quality Scorer    │   │
  │   └───────────────┘        └───────────────────┘        └────────────┬─────────────┘   │
  │                                                                      │                 │
  │                                                                      ▼                 │
  │   ┌───────────────┐        ┌───────────────────┐        ┌──────────────────────────┐   │
  │   │ Safety Engine │◀───────│  Evidence Engine  │◀───────│    Inference Provider    │   │
  │   │(Conflict/Pol) │        │ (Verbatim Matcher)│        │(Rule-Based / ROCm / vLLM)│   │
  │   └───────┬───────┘        └───────────────────┘        └──────────────────────────┘   │
  │           │                                                                            │
  │           ▼                                                                            │
  │   ┌───────────────┐        ┌───────────────────┐                                       │
  │   │ Care Plan Gen │───────▶│Translation Service│                                       │
  │   └───────────────┘        │ (6 Indian Langs)  │                                       │
  │                            └───────────────────┘                                       │
  └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technologies | Rationale |
|---|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons | High-performance server/client rendering, responsive mobile/desktop design, strict CSP headers. |
| **Backend API** | FastAPI, Python 3.10+, Pydantic v2, Uvicorn, Python-Multipart | Asynchronous, typed endpoints, automated OpenAPI documentation, sub-millisecond route dispatching. |
| **Database** | SQLAlchemy 2.0 declarative models, Alembic migrations | Dual compatibility: Zero-config SQLite for local development; PostgreSQL for production deployments. |
| **Document Processing** | PyPDF, Tesseract OCR, Pillow | Secure extraction of multi-page PDF documents and photographic image scans with quality scoring. |
| **Inference Engine** | Pluggable: `rule_based` (default), `openai_compat` (AMD ROCm / vLLM / NVIDIA / Cloud) | Zero-cost deterministic rule-based extractor by default; seamless high-throughput GPU inference when available. |
| **Multilingual** | Deep-Translator & Google Cloud Translation v2 API | Translates verified patient guidance into Hindi, Gujarati, Marathi, Tamil, and Telugu with entity masking. |
| **Authentication** | Firebase Auth (client) + JWT verification (API) | Secure token verification with deterministic UUID user mapping and isolated patient data scopes. |

---

## 5. Prerequisites

Before installing, ensure your system has:
- **Python:** Version 3.10 or higher (Python 3.12 recommended).
- **Node.js:** Version 18 or higher (Node.js 20+ recommended) and `npm`.
- **Git**

---

## 6. Single-Command Setup & Startup

CARELYNX includes unified single-file setup and startup scripts that automate the entire workflow across **Linux**, **macOS**, and **Windows**.

### 6.1 Step 1: Automated Dependency Setup (Run Once)

The setup script automatically:
- Creates your local `.env` configuration from `.env.example` (if not present).
- Configures the Python virtual environment in `apps/api/.venv`.
- Downloads and installs all backend Python dependencies (FastAPI, SQLAlchemy, Alembic, ReportLab, PyPDF, etc.).
- Downloads and installs all frontend Node.js packages (Next.js, React 19, Tailwind, Lucide, Firebase).
- Executes Alembic database migrations.
- Generates realistic sample discharge and conflict PDFs for immediate offline testing.

**Execute the setup command for your operating system:**

| Operating System | Single Command |
|---|---|
| **Linux / macOS (Bash)** | `./setup.sh` |
| **Windows (Command Prompt)** | `setup.bat` |
| **Windows (PowerShell)** | `.\setup.ps1` |
| **Cross-Platform (Python)** | `python run.py setup` |

---

### 6.2 Step 2: Automated Startup (Start Full Stack)

The startup script concurrently boots the FastAPI backend on port 8000 and the Next.js frontend on port 3000 with unified colorized logging and clean CTRL+C shutdown:

| Operating System | Single Command |
|---|---|
| **Linux / macOS (Bash)** | `./run_dev.sh` |
| **Windows (Command Prompt)** | `run_dev.bat` |
| **Windows (PowerShell)** | `.\run_dev.ps1` |
| **Cross-Platform (Python)** | `python run.py dev` |

> [!TIP]
> **Zero-Friction Auto-Setup:** If you run `./run_dev.sh` before running setup, it will automatically detect the missing virtual environment and run the full setup for you before starting the services!

---

## 7. Application Access Points & URLs

Once started, access the application in your browser:

| Service / Interface | URL | Description |
|---|---|---|
| **Patient Care Portal** | [http://localhost:3000](http://localhost:3000) | Document upload, processing status, timeline, medication schedule, multilingual switch, voice readout. |
| **Clinical Reviewer Workspace** | [http://localhost:3000/review](http://localhost:3000/review) | Triage queue, side-by-side document comparator, conflict adjudication, fact verification. |
| **API Interactive Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI 3.0 interactive documentation and test console for all backend REST endpoints. |
| **Backend Health Check** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Real-time diagnostic status for database connection, hardware provider, and inference engine. |

---

## 8. Granular Service Commands & Testing

For specialized workflows, you can control services independently:

```bash
# Start FastAPI backend server only (http://localhost:8000)
python run.py api

# Start Next.js frontend server only (http://localhost:3000)
python run.py web

# Run complete backend unit and integration test suite (143+ tests)
python run.py test

# Run full end-to-end QA probe and security vulnerability suite
python qa_test_suite.py

# Generate sample medical records and conflicting prescriptions
python run.py generate-samples
```

---

## 9. Configuration & Security

CARELYNX ships with sensible defaults that require **zero configuration** for local development.

### Local Environment Setup
When setup runs, it creates `.env` from `.env.example`:
```bash
cp .env.example .env    # Created automatically by ./setup.sh
```

### Key Environment Options
| Variable | Default | Purpose |
|---|---|---|
| `ENVIRONMENT` | `development` | App environment (`development` / `production`). |
| `DATABASE_URL` | *(empty = SQLite)* | Set to `postgresql+psycopg://user:pass@host:5432/db` for PostgreSQL. |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed web frontend origin(s). |
| `INFERENCE_PROVIDER` | `rule_based` | `rule_based` (local, zero-cost) or `openai_compat` (GPU / vLLM / Cloud). |
| `INFERENCE_BASE_URL` | `http://localhost:8080/v1` | Endpoint URL for `openai_compat` inference. |
| `INFERENCE_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | Model identifier passed to inference server. |
| `GOOGLE_TRANSLATE_API_KEY` | *(optional)* | Optional Google Cloud Translation v2 key for high-throughput Indian language translation. |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | URL where the web client accesses the backend. |

> [!IMPORTANT]
> **Security & Privacy Commitment:**  
> - `.env` is permanently excluded from version control via `.gitignore`.
> - Never commit private API keys, database passwords, or personal credentials.
> - Patient documents uploaded during testing are stored in private local folders (`apps/api/var/storage/`) that are strictly excluded from git tracking.

---

## 10. Production Deployment

CARELYNX is architected for simple deployment to modern cloud platforms:

### Option A: Railway (Backend) + Vercel (Frontend)
1. **Backend on Railway:**
   - Deploy `apps/api` using Railway's PostgreSQL template and Nixpacks/Dockerfile.
   - Configure environment variables using `apps/api/.env.railway.example`.
2. **Frontend on Vercel:**
   - Deploy `apps/web` to Vercel with root directory set to `apps/web`.
   - Set `NEXT_PUBLIC_API_BASE_URL` to your live Railway backend URL.

### Option B: Docker Compose (Self-Hosted / GPU Box)
A production-ready `docker-compose.yml` runs the entire stack (Caddy reverse proxy with automatic HTTPS, Next.js frontend, FastAPI backend, and PostgreSQL 16):

```bash
# 1. Prepare configuration
cp .env.example .env

# 2. Start full stack (CPU / Rule-Based)
docker compose up -d --build

# 3. Start with AMD ROCm vLLM GPU acceleration (requires AMD GPU with ROCm)
docker compose --profile amd up -d --build

# 4. Start with NVIDIA CUDA GPU acceleration
docker compose --profile nvidia up -d --build
```

---

## 11. Project Directory Structure

```text
CARELYNX/
├── apps/
│   ├── api/                          # FastAPI Backend Application
│   │   ├── alembic/                  # Database migration scripts
│   │   ├── app/                      # Application core, models, schemas, and routes
│   │   │   ├── api/v1/               # REST endpoint handlers (cases, documents, reviews)
│   │   │   ├── core/                 # Auth, config, security, and exception handlers
│   │   │   ├── models/               # SQLAlchemy declarative ORM models
│   │   │   ├── schemas/              # Pydantic validation schemas
│   │   │   └── services/             # Pipeline, OCR, evidence, and safety engines
│   │   ├── tests/                    # 143+ unit, integration, and safety tests
│   │   ├── Dockerfile                # Production container specification
│   │   └── requirements.txt          # Backend Python dependencies
│   └── web/                          # Next.js Frontend Web Application
│       ├── app/                      # Next.js App Router (pages, layout, styles)
│       │   ├── page.tsx              # Patient Care Portal & timeline
│       │   └── review/page.tsx       # Clinical Reviewer Workspace
│       ├── lib/                      # API client, Firebase auth, helper utilities
│       ├── public/                   # Favicons, logos, and web manifest
│       └── package.json              # Frontend Node.js dependencies
├── docs/                             # Complete architecture & clinical safety specs
├── infra/                            # Hardware benchmarks and GPU orchestration (AMD/NVIDIA)
├── requirements.txt                  # Unified root Python dependency manifest
├── run.py                            # Cross-platform CLI runner and task engine
├── setup.sh                          # Single-command setup (Linux / macOS)
├── setup.bat                         # Single-command setup (Windows CMD)
├── setup.ps1                         # Single-command setup (Windows PowerShell)
├── run_dev.sh                        # Single-command startup (Linux / macOS)
├── run_dev.bat                       # Single-command startup (Windows CMD)
├── run_dev.ps1                       # Single-command startup (Windows PowerShell)
└── docker-compose.yml                # Multi-container orchestration (Caddy + API + Web + DB)
```

---

## 12. Complete Documentation Reference (`/docs`)

For in-depth architectural and safety specifications, consult the documents in [`docs/`](docs/):

| Document | Description |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | **Product Requirements Document:** Vision, personas, MVP scope, and clinical non-goals. |
| [`docs/SRS.md`](docs/SRS.md) | **Software Requirements Specification:** Functional requirements (FR-001–FR-017) and error taxonomy. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | **System Architecture:** Detailed component design, AMD ROCm integration, and database ERD. |
| [`docs/SAFETY.md`](docs/SAFETY.md) | **Safety Guardrails:** Verbatim evidence linking invariants, conflict triggers, and OCR policies. |
| [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md) | **API Contracts:** Request/response schemas, role headers, and error definitions for all endpoints. |
| [`docs/DATABASE.md`](docs/DATABASE.md) | **Database Specification:** Entity schemas, UUID types, UTC timestamps, and migration instructions. |
| [`docs/TEAM.md`](docs/TEAM.md) | **Team Charter:** Role responsibilities (Frontend, Backend, AI/QA) and domain ownership. |
| [`docs/AI_INSTRUCTIONS.md`](docs/AI_INSTRUCTIONS.md) | **AI Agent Operating Rules:** Operating rules and pre-flight checklist for pair programming agents. |
| [`docs/AI_LOG.md`](docs/AI_LOG.md) | **AI Development Log:** Immutable audit trail of engineering tasks and commits. |

---

## 13. License

Internal Hackathon Project. All rights reserved.
