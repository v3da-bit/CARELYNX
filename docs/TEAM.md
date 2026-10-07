# CARELYNX — Team Charter & Member Instructions

> **Document Version:** 1.0.0  
> **Location:** `/docs/TEAM.md`  
> **Team Composition:** 3 Human Engineers + AI Collaborative Assistants  

---

## 1. Team Overview & Mission

CARELYNX is engineered by a close-knit group of **3 developers** who pair-program with AI assistants to build a production-grade healthcare document navigation platform. 

Our team operates under a shared code-of-conduct:
1. **Single Source of Truth:** All technical and product decisions adhere strictly to `/docs` (derived from `/docs copy`).
2. **Specialized Ownership:** Every member has designated ownership, with dedicated focus on their respective domain.
3. **AI as a Disciplined Multiplier:** AI assistants are used extensively, but they must follow strict project guidelines, avoid conceptual drift, and record every change in `docs/AI_LOG.md`.

---

## 2. Team Roster & Roles

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CARELYNX TRIAD TEAM                             │
├──────────────────────┬─────────────────────────┬───────────────────────┤
│ Member 1: Frontend   │ Member 2: Backend       │ Member 3: AI & QA     │
│ Lead UI/UX Engineer  │ Systems & Data Engineer │ Inference & Safety    │
├──────────────────────┼─────────────────────────┼───────────────────────┤
│ • Next.js App Router │ • FastAPI Services      │ • AI Provider Engine  │
│ • Tailwind CSS / UI  │ • SQLAlchemy & Alembic  │ • Safety Guardrails   │
│ • Evidence Drawer    │ • Storage Abstraction   │ • AMD ROCm Runtime    │
│ • Reviewer Workspace │ • API Contracts & DB    │ • Evaluation Scenarios│
└──────────────────────┴─────────────────────────┴───────────────────────┘
```

---

### Member 1: Dedicated Frontend Developer (Lead UI/UX Engineer)
- **Assigned Member Name:** `[Member 1 Name — e.g., Alex / Frontend Lead]`
- **Primary Domain:** `apps/web/`
- **Core Technologies:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide React.
- **Key Responsibilities:**
  - Lead the end-to-end design, usability, and visual excellence of the web application.
  - Architect and maintain patient-facing experiences: Document Upload Dropzone, Real-time Processing Feed, Care Plan Timeline, Medication Cards, and Multilingual Selector.
  - Architect and maintain clinical reviewer experiences: `/review` route, Side-by-Side Document Comparator, Conflict Resolution Modal, and Audit Viewer.
  - Maintain typed API client interactions in `apps/web/lib/api.ts`.
  - Ensure strict accessibility standards (high contrast, keyboard navigability, clear clinical state indicators).

#### Specific Instructions for Member 1 (Frontend Lead):
1. **Maintain Consistent Design Language:**
   - Use clean, medical-grade styling: neutral slates, calming teals/blues for verified items, cautionary ambers for review alerts, and clean crimson for critical conflicts.
   - Avoid generic, unstyled inputs; all modals, drawers, and buttons must have explicit hover, active, and focus states.
2. **Enforce API Type Safety:**
   - Always ensure TypeScript types in `apps/web/lib/api.ts` mirror the Pydantic schemas in `apps/api/app/schemas/`.
   - Never bypass error contracts; properly render `UPLOAD_ERROR`, `EVIDENCE_ERROR`, and `CONFLICT_ERROR` with user-friendly banners.
3. **Guiding AI on Frontend Tasks:**
   - When instructing an AI to create or edit frontend components, explicitly remind it of our Tailwind conventions and component boundaries.
   - Do not allow AI to install bloated external component libraries (like shadcn/radix/material) unless explicitly agreed upon with the team; keep the codebase lightweight and performant.

---

### Member 2: Backend & Systems Engineer (Lead Data & Storage Engineer)
- **Assigned Member Name:** `[Member 2 Name — e.g., Sarah / Backend Lead]`
- **Primary Domain:** `apps/api/` (Core, DB, API routes, Repositories, Storage)
- **Core Technologies:** Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, SQLite / PostgreSQL.
- **Key Responsibilities:**
  - Maintain API application factory, routing architecture, and security middlewares in `apps/api/app/main.py` and `app/api/v1/`.
  - Manage database schemas, Alembic migrations, and SQLite/PostgreSQL parity in `apps/api/app/db/` and `app/models/`.
  - Oversee document ingestion, validation (magic bytes, size limits), and private storage in `apps/api/app/storage/`.
  - Enforce audit trail logging for all case events and reviewer resolutions.

#### Specific Instructions for Member 2 (Backend Lead):
1. **Protect Database & Storage Invariants:**
   - All table primary keys must remain UUIDv4; all timestamps must be stored in UTC (`TIMESTAMPTZ` / ISO 8601 strings).
   - Ensure `LocalPrivateStorage` stores files outside public roots and uses non-predictable hashed keys.
2. **Keep Endpoints Synchronized with Contracts:**
   - Cross-check all router modifications with `docs/API_CONTRACTS.md`.
   - Ensure proper role-header verification (`X-Carelynx-Role: reviewer`) on protected reviewer endpoints.
3. **Guiding AI on Backend Tasks:**
   - Require AI to run database migration checks or local tests whenever models or repositories are touched.
   - Never let AI expose raw tracebacks or internal paths in API error responses.

---

### Member 3: AI, Safety & Evaluation Lead (Lead Inference & QA Engineer)
- **Assigned Member Name:** `[Member 3 Name — e.g., Ryan / AI & QA Lead]`
- **Primary Domain:** `apps/api/app/ai/`, `apps/api/app/safety/`, `infra/amd/`, evaluation scripts.
- **Core Technologies:** Python, vLLM / PyTorch, ROCm / AMD hardware integration, Pydantic, regex rule engines.
- **Key Responsibilities:**
  - Own the `InferenceProvider` abstraction (`rule_based` vs `openai_compatible`).
  - Maintain prompt templates in `apps/api/app/ai/prompts/` and ensure structured JSON output parsing.
  - Direct the verbatim evidence matcher and deterministic conflict detection engine.
  - Manage AMD ROCm deployment scripts, GPU benchmark scripts, and evaluation scenarios.

#### Specific Instructions for Member 3 (AI & Safety Lead):
1. **Zero Hallucination Policy:**
   - Audit AI extraction routines to ensure non-medical or unmentioned fields are never hallucinated.
   - Ensure evidence snippets match verbatim source page text before facts can transition to `VERIFIED`.
2. **AMD Hardware Portability:**
   - Ensure the system runs out-of-the-box in local dev using `rule_based` provider, while providing a tested, production-grade vLLM path for AMD GPUs.
3. **Guiding AI on Inference Tasks:**
   - Never allow an AI assistant to hardcode fake clinical data fallbacks. If extraction fails, it must fail explicitly with structured errors or trigger review.

---

## 3. Collaborative Workflow for the 3-Person Team

### 3.1 Daily Workflow & Task Handshakes
```text
┌─────────────────────────┐
│ Member 2: Backend Lead  │
│ Delivers API Endpoint   │ ──(API Contract JSON)──▶ ┌─────────────────────────┐
└─────────────────────────┘                          │ Member 1: Frontend Lead │
                                                     │ Builds UI & Views       │
┌─────────────────────────┐                          └─────────────────────────┘
│ Member 3: AI/Safety Lead│                                      ▲
│ Delivers Extraction     │ ──(Structured Fact Stream)───────────┘
└─────────────────────────┘
```

1. **Before Starting Any Feature:**
   - Discuss interface changes across team members.
   - Update `docs/API_CONTRACTS.md` or `docs/DATABASE.md` first before writing code.
2. **Branch & Commit Hygiene:**
   - Use descriptive git commit messages: `feat(web): add evidence drawer`, `fix(api): correct magic byte validation`.
3. **Running Local Services:**
   - Backend terminal: `cd apps/api && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
   - Frontend terminal: `cd apps/web && npm run dev -- -H 0.0.0.0`

---

## 4. Instructions for Working with AI Assistants

As a team utilizing AI coding agents (Claude, Gemini, ChatGPT, Antigravity):

1. **Mandatory AI Onboarding:**
   - Every AI assistant **MUST** read `docs/AI_INSTRUCTIONS.md` before starting any coding task.
2. **No Unapproved Architectural Pivots:**
   - AIs must NOT introduce new frameworks (e.g., swapping Next.js for Vue, or FastAPI for Express).
   - AIs must NOT change the product scope (e.g., turning Carelynx into an EHR, a telemedicine video app, or a symptom-checker diagnostic bot).
3. **Mandatory Post-Task Commit Logging:**
   - Whenever an AI finishes a task, it **MUST** append an entry to `docs/AI_LOG.md` formatted strictly as a git commit.
4. **Human Review of AI Output:**
   - The dedicated frontend developer reviews all UI code written by AI to maintain visual polish and user experience integrity.
   - The backend lead reviews database queries, migrations, and endpoint security.
   - The AI lead inspects prompt templates, model configurations, and safety policies.
