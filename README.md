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
6. **Patient Care Plan:** Displays an intuitive chronological timeline, categorized care instructions, and multilingual toggles (English, Hindi, Gujarati).
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

## 6. Quickstart & Setup Guide

### 6.1 Prerequisites
- **Node.js:** v18+ (v20+ recommended)
- **Python:** 3.10+ (tested with Python 3.12)
- **Git**

### 6.2 Environment Configuration
Copy the sample environment configuration:
```bash
cp .env.example .env
```

### 6.3 Backend Setup (FastAPI)
The backend runs on FastAPI and uses a zero-configuration SQLite database (`carelynx.db`) by default for local development.

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the development API server on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check verification:
```bash
curl http://localhost:8000/api/v1/health
```

### 6.4 Frontend Setup (Next.js)
The frontend uses Next.js App Router, React 19, and Tailwind CSS.

```bash
cd apps/web
npm install

# Start the web development server on port 3000
npm run dev -- -H 0.0.0.0
```

Open your browser to:
- **Patient Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Clinical Reviewer Workspace:** [http://localhost:3000/review](http://localhost:3000/review)
- **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 7. AMD ROCm Hardware Deployment

CARELYNX includes native support for AMD-accelerated inference:
1. Start an OpenAI-compatible vLLM server on an AMD ROCm system:
   ```bash
   docker compose -f infra/amd/docker-compose.rocm.yml up -d
   ```
2. Configure `.env`:
   ```env
   INFERENCE_PROVIDER=openai_compatible
   OPENAI_COMPATIBLE_BASE_URL=http://localhost:8080/v1
   OPENAI_COMPATIBLE_MODEL=meta-llama/Llama-3-8B-Instruct
   ```
3. Restart the API server. Inferences will execute directly on AMD GPUs.

---

## 8. License

Internal Hackathon Project. All rights reserved.
