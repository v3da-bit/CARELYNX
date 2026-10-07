# CARELYNX — System Architecture

> **Document Version:** 1.1.0  
> **Source of Truth:** `/docs/ARCHITECTURE.md` (Synced with `/docs copy/ARCHITECTURE.md`)  
> **Target Audience:** Engineering Team & AI Coding Assistants  

---

## 1. Architectural Mission

Build a modular, evidence-first healthcare document processing platform where AI assists with extraction and communication but does **not** autonomously make clinical decisions.

### Architectural Philosophy
1. **Evidence-First:** Every clinical claim must originate from a verified verbatim source snippet.
2. **Deterministic Safety:** Safety policies, conflict detection, and status transitions reside in deterministic application code, not probabilistic LLM outputs.
3. **Decoupled AI Engine:** Abstract inference provider interface allowing local rule-based dev, cloud LLMs, or local AMD ROCm-powered vLLM nodes.
4. **Resilient Persistence:** Dual-engine DB design targeting PostgreSQL for production while gracefully running locally on SQLite with zero external dependencies.

---

## 2. High-Level System Architecture

```text
                           ┌────────────────────────────┐
                           │      Next.js Frontend      │
                           │   (App Router, TS, Tailwind)│
                           │    Patient & Reviewer UI   │
                           └─────────────┬──────────────┘
                                         │ HTTPS / REST (JSON)
                                         ▼
                           ┌────────────────────────────┐
                           │      FastAPI Backend       │
                           │  (App Factory, Middlewares)│
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

## 3. Core Subsystems & Responsibilities

### 3.1 Web Tier (`apps/web`)
- **Technology:** Next.js (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons.
- **Key Modules:**
  - `app/page.tsx`: Patient portal containing document upload, progress indicators, care plan timeline, medication list, and multilingual selector.
  - `app/review/page.tsx`: Clinical reviewer workspace displaying flagged conflicts, side-by-side document views, and resolution controls.
  - `lib/api.ts`: Typed API client handling all requests, error mapping, and role headers (`X-Carelynx-Role`).

### 3.2 API Tier (`apps/api/app`)
- **Technology:** FastAPI, Pydantic v2, Python 3.10+, Uvicorn.
- **Layers:**
  - `api/v1/`: Thin HTTP routers validating payloads and mapping status codes.
  - `services/`: Core domain orchestration (document pipeline, conflict detection, review lifecycle, translation).
  - `repositories/`: Database abstraction handling model CRUD.
  - `models/`: Declarative SQLAlchemy models.
  - `schemas/`: Pydantic input/output validation contracts.

### 3.3 Storage Abstraction (`apps/api/app/storage`)
- **Protocol:** `StorageBackend` (`put`, `get`, `delete`, `exists`).
- **Implementations:**
  - `LocalPrivateStorage`: Stores files in an isolated directory (`./storage_root`) with hashed storage keys. Files are never served statically.
  - `S3Storage` / `SupabaseStorage`: Cloud-ready drop-in replacement.

### 3.4 Inference Abstraction (`apps/api/app/ai`)
- **Protocol:** `InferenceProvider` (`extract_facts`, `health_check`).
- **Implementations:**
  - `RuleBasedProvider`: Fast, deterministic regex & heuristic parser for local testing and zero-GPU environments.
  - `OpenAICompatibleProvider`: Standard completions client configured for AMD ROCm-hosted vLLM or local LLM instances.
- **Prompt Isolation:** Prompt templates versioned under `apps/api/app/ai/prompts/` (e.g. `extraction_v1.md`).

### 3.5 Evidence & Safety Engine (`apps/api/app/safety`)
- **Verbatim Matcher:** Verifies that every extracted snippet appears identically on the cited source page.
- **Deterministic Policy:** Enforces strict prohibitions against diagnostic speculation, unauthorized dose modifications, or hallucinated facts.
- **Conflict Detector:** Computes equality and compatibility between facts across different documents within the same case.

---

## 4. AMD Hardware & ROCm Integration

For hackathon deployments and edge clinical workloads, CARELYNX integrates with AMD computing hardware:
- **Runtime:** vLLM running on AMD ROCm (Radeon / Instinct / Ryzen AI).
- **Communication:** Standard OpenAI-compatible REST API exposed over local network.
- **Configuration:** Controlled via `.env` settings:
  ```env
  INFERENCE_PROVIDER=openai_compatible
  OPENAI_COMPATIBLE_BASE_URL=http://localhost:8080/v1
  OPENAI_COMPATIBLE_MODEL=meta-llama/Llama-3-8B-Instruct
  OPENAI_COMPATIBLE_API_KEY=not-needed
  ```
- **Fallback Guarantee:** If AMD hardware is offline or during developer unit testing, the system automatically falls back to `RuleBasedProvider` without crashing or blocking the UI.

---

## 5. Database Schema & Data Models

All primary keys are UUIDv4. All timestamps are UTC (`TIMESTAMPTZ` in Postgres, converted appropriately in SQLite).

```text
  ┌──────────────┐          1:N          ┌──────────────┐
  │   patients   │──────────────────────▶│    cases     │
  └──────────────┘                       └──────┬───────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 │ 1:N                          │ 1:N                          │ 1:N
                 ▼                              ▼                              ▼
          ┌──────────────┐               ┌──────────────┐               ┌──────────────┐
          │  documents   │               │    facts     │               │  conflicts   │
          └──────┬───────┘               └──────┬───────┘               └──────────────┘
                 │ 1:N                          │ 1:N
                 ▼                              ▼
          ┌──────────────┐               ┌──────────────┐
          │document_pages│               │   evidence   │
          └──────────────┘               └──────────────┘
                 │                              │
                 └──────────────┬───────────────┘
                                ▼
                         ┌──────────────┐
                         │ review_cases │
                         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  audit_logs  │
                         └──────────────┘
```

---

## 6. Execution Lifecycle for Document Ingestion

```text
Client (Web)                  FastAPI Router                  Document Pipeline            Database / Storage
     │                              │                                │                             │
     │── POST /api/v1/documents ───▶│                                │                             │
     │   (multipart file)           │── Validate magic bytes ───────▶│                             │
     │                              │── Store file in storage ───────┼────────────────────────────▶│
     │                              │── Create document record ──────┼────────────────────────────▶│
     │◀─ 201 Created (document_id) ─│                                │                             │
     │                              │                                │                             │
     │── POST /documents/{id}/proc ─▶│                                │                             │
     │                              │── Run extraction pipeline ────▶│                             │
     │                              │                                │── Extract pages (pypdf)     │
     │                              │                                │── Run OCR if scanned        │
     │                              │                                │── Score text quality        │
     │                              │                                │── InferenceProvider extract │
     │                              │                                │── Verbatim evidence check   │
     │                              │                                │── Safety policy check       │
     │                              │                                │── Detect multi-doc conflict │
     │                              │                                │── Save facts & evidence ───▶│
     │                              │                                │── Create review if needed ─▶│
     │◀─ 200 OK (Status) ───────────│                                │                             │
```

---

## 7. Security & Compliance Invariants

1. **Least-Privilege Role Gating:** Restricted routes (e.g. `/api/v1/reviews/*`) require the `X-Carelynx-Role: reviewer` header.
2. **Storage Isolation:** Uploaded medical records are stored with randomized UUID keys, never accessible directly by URL or static route.
3. **No Clinical Hallucination:** Zero clinical advice generation. If a document does not mention an item, the model cannot supply one.
4. **Data Sanitization:** Passwords, keys, and raw clinical document blobs are excluded from application logs.
