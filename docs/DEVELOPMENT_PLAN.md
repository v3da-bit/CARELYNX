# CARELYNX — Development & Execution Plan

> **Document Version:** 1.1.0  
> **Source of Truth:** `/docs/DEVELOPMENT_PLAN.md`  
> **Status:** MVP Core Complete (Phases 0–10 Implemented and Operational)  

---

## Roadmap & Milestone Overview

```text
Phase 0 ──▶ Phase 1 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4 ──▶ Phase 5 ──▶ Phase 6 ──▶ Phase 7 ──▶ Phase 8 ──▶ Phase 9 ──▶ Phase 10
Bootstrap   Upload      Processing  Extraction  Evidence    Care Plan   Multilingual Review      AMD ROCm    Evaluation  Demo Prep
[DONE]      [DONE]      [DONE]      [DONE]      [DONE]      [DONE]      [DONE]       [DONE]      [DONE]      [DONE]      [ACTIVE]
```

---

## Phase Details & Deliverables

### Phase 0: Repository & Environment Bootstrap ✅
- **Goal:** Establish runnable monorepo with FastAPI backend, Next.js frontend, and database configuration.
- **Deliverables:**
  - `apps/api`: FastAPI factory, `/api/v1/health`, security middleware, CORS.
  - `apps/web`: Next.js 16 App Router shell, Tailwind CSS configuration.
  - `.env.example`, `docker-compose.yml`, initial Alembic structure.
- **Status:** **Completed**

### Phase 1: Secure Document Intake ✅
- **Goal:** Ingestion pipeline supporting PDF, PNG, and JPEG documents.
- **Deliverables:**
  - Multipart upload endpoint (`POST /api/v1/documents`).
  - Magic-byte validation (`upload_validation.py`) rejecting corrupted or malicious files.
  - `StorageBackend` abstraction with `LocalPrivateStorage` storing files in isolated disk keys.
- **Status:** **Completed**

### Phase 2: Page-Aware Extraction & OCR Engine ✅
- **Goal:** Split documents into 1-indexed pages and compute text quality scores.
- **Deliverables:**
  - Native digital extraction via `pypdf`.
  - Fallback OCR protocol (`TesseractOcr` / `UnavailableOcr`).
  - Deterministic text quality score based on garbled tokens and confusable characters.
- **Status:** **Completed**

### Phase 3: Structured Clinical Fact Extraction ✅
- **Goal:** Parse text into typed entities (follow-ups, medications, instructions, warnings).
- **Deliverables:**
  - `InferenceProvider` abstraction with `RuleBasedProvider` and `OpenAICompatibleProvider`.
  - Pydantic fact models and structured JSON prompt templates.
  - Strict document validation filter to eliminate fake data fallbacks.
- **Status:** **Completed**

### Phase 4: Verbatim Evidence & Deterministic Safety Engine ✅
- **Goal:** Ensure every fact links to verifiable source text and detect discrepancies.
- **Deliverables:**
  - Substring evidence matcher confirming snippets exist verbatim on source pages.
  - Deterministic status calculator (`safety/status.py`) assigning `VERIFIED`, `NEEDS_REVIEW`, `CONFLICT_DETECTED`.
  - Multi-document conflict detection engine (`conflicts.py`).
- **Status:** **Completed**

### Phase 5: Patient Care Plan Interface ✅
- **Goal:** Turn verified facts into a clear, accessible patient experience.
- **Deliverables:**
  - `apps/web/app/page.tsx` with document upload dropzone, processing progress ticker, timeline view, and medication cards.
  - Interactive slide-over evidence drawer showing the exact page snippet.
- **Status:** **Completed**

### Phase 6: Multilingual Translation Support ✅
- **Goal:** Enable care plan communication in English (`en`), Hindi (`hi`), and Gujarati (`gu`).
- **Deliverables:**
  - Translation service preserving dates, dosages, and uncertainty indicators without fact distortion.
  - Frontend language selector toggle.
- **Status:** **Completed**

### Phase 7: Clinical Reviewer Dashboard ✅
- **Goal:** Provide clinical staff with tools to inspect and resolve flagged items.
- **Deliverables:**
  - `/review` workspace displaying open conflict tickets and low-confidence pages.
  - Side-by-side evidence inspection.
  - Decision submission API (`POST /api/v1/reviews/{id}/resolve`) and immutable audit logs.
- **Status:** **Completed**

### Phase 8: AMD ROCm Hardware Integration ✅
- **Goal:** Run clinical inference on AMD GPU / ROCm infrastructure.
- **Deliverables:**
  - `OpenAICompatibleProvider` connecting to local vLLM instances hosted on AMD hardware.
  - Deployment configurations under `infra/amd/`.
- **Status:** **Completed**

### Phase 9: Evaluation & Benchmarking ✅
- **Goal:** Measure extraction accuracy, evidence precision, and conflict detection recall.
- **Deliverables:**
  - Synthetic medical benchmark cases and evaluation scripts.
- **Status:** **Completed**

### Phase 10: Demo Hardening & Team Synchronization 🔄
- **Goal:** Ensure complete team alignment across the 3 developers, synchronize documentation, and prepare the live hackathon walkthrough.
- **Deliverables:**
  - Fully synchronized `/docs` directory matching `/docs copy`.
  - Comprehensive `TEAM.md`, `AI_INSTRUCTIONS.md`, and `AI_LOG.md`.
  - Robust root `README.md`.
- **Status:** **Active & Current Focus**
