# CARELYNX — System Architecture

> **Document Version:** 1.2.0  
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
 │   └───────────────┘        │ en/hi/gu/mr/ta/te │                               │
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
  - `lib/api.ts`: Typed API client handling all requests and error mapping; reviewer calls send `X-Carelynx-Role: reviewer`.

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
  - `LocalPrivateStorage`: Stores files in an isolated directory (`STORAGE_LOCAL_DIR`, default `apps/api/var/storage`) with random storage keys. Files are never served statically. **This is the only implemented backend.**
  - S3-compatible / Supabase storage: planned drop-in behind the same protocol — **not implemented**.

### 3.4 Inference Abstraction (`apps/api/app/ai`)
- **Protocol:** `InferenceProvider` (`app/ai/provider.py`): `info: ProviderInfo(name, model, hardware_label)`, `async generate_structured(StructuredRequest) -> dict`, `async generate_text(system_prompt, user_prompt) -> str`. Providers return raw output; failures raise `ProviderError`. Selected by `INFERENCE_PROVIDER` (`app/ai/factory.py`).
- **Implementations:**
  - `RuleBasedProvider` (default): deterministic, page-aware extractor. Reads the real page texts from `request.context["pages"]` and recognises document *shapes* (labelled fields, list items under headings, `<name> <dose><unit> …` medication lines, label/value table rows) — no drug-name list, no invented values. Quotes are verbatim slices of the page they cite; OCR-damaged text is reported with `legible=false` and unreadable fields `null`. Cannot generate free text.
  - `OpenAICompatibleProvider` (`openai_compat`): `/v1/chat/completions` client with `response_format: json_schema`, for vLLM on AMD ROCm (or any compatible endpoint). Never falls back silently.
- **Fallback policy (`app/services/extraction.py::run_extraction`):** if a non-rule-based provider fails (network, malformed JSON, schema violation) the rule-based extractor is used and facts record `extracted_by = "rule_based (fallback from openai_compat)"`, with an audit event. If that also fails → `ProviderError` → `502 MODEL_ERROR`.
- **Prompt Isolation:** versioned prompts under `apps/api/app/ai/prompts/` (`extraction_v1.md`, `translation_v1.md`), each stating role, task, allowed information, forbidden behaviour, output schema, evidence and abstention rules.

### 3.5 Evidence & Safety Engine (`apps/api/app/safety`, `app/services/conflicts.py`)
- **Verbatim Matcher:** Verifies that every extracted snippet appears identically on the cited source page (relocating to the real page if needed).
- **Deterministic Status & Confidence:** `status.py` computes status and an application-level confidence from page quality, OCR confidence, quote quality, legibility, evidence and key-field parsing (SAFETY.md §2.1).
- **Deterministic Policy:** `policy.py` rejects generated advice, dose-change and diagnosis language that is not literally in the verified source quote.
- **Conflict Detector:** groups facts by `(fact_type, subject)`, compares normalised values, never picks a winner, opens HIGH reviews (SAFETY.md §3).

### 3.6 Translation (`apps/api/app/services/translation.py`)
`GET /cases/{id}/care-plan?lang=xx` (care-plan service) sends only `VERIFIED` display text to `translate_texts(texts, lang, protected_terms=drug names)`:

```text
mask drug names / doses / dates / times / phones / numbers → placeholder tokens
  → Google Cloud Translation v2 (if GOOGLE_TRANSLATE_API_KEY)
  → openai_compat LLM with translation_v1 prompt (if INFERENCE_PROVIDER != rule_based)
  → free Google web endpoint (deep-translator)
unmask → verify every token returned exactly once and digits unchanged → else None ("unavailable", English shown)
```
10 s budget per batch; failures never raise; in-process cache keyed by (text, language, protected terms).

## 4. AMD Hardware & ROCm Integration

- **Runtime:** vLLM on ROCm serving `Qwen/Qwen2.5-7B-Instruct` (`infra/amd/docker-compose.rocm.yml`, port 8080), reached through `OpenAICompatibleProvider`.
- **Configuration** (`.env`, see `.env.example` and `infra/amd/README.md`):
  ```env
  INFERENCE_PROVIDER=openai_compat
  INFERENCE_BASE_URL=http://localhost:8080/v1
  INFERENCE_MODEL=Qwen/Qwen2.5-7B-Instruct
  INFERENCE_HARDWARE_LABEL=amd-rocm-vllm   # only when the endpoint really runs on an AMD GPU
  ```
- **Measurement:** `infra/amd/benchmark_rocm.py` benchmarks the real extraction prompt on the endpoint and labels results "AMD GPU (ROCm)" only when `rocm-smi`/`amd-smi` detect an AMD GPU on the same host; `apps/api/scripts/evaluate_clinical.py --provider openai_compat` scores scenarios A/B/C with the LLM.
- **Status:** the ROCm path is implemented and deployable but has **not** been executed on AMD hardware from this repository's development machines; all committed results are CPU rule-based results and are labelled as such.
- **Fallback:** if the endpoint is unavailable, extraction falls back to `RuleBasedProvider` with truthful provenance (§3.4).

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

1. **Least-Privilege Reviewer Access:** Restricted routes (`/api/v1/reviews/*`, `/cases/{id}/audit`) require the `X-Carelynx-Role: reviewer` header (demo boundary; see API_CONTRACTS §1.1).
2. **Storage Isolation:** Uploaded medical records are stored with randomized UUID keys, never accessible directly by URL or static route.
3. **No Clinical Hallucination:** Zero clinical advice generation. If a document does not mention an item, the model cannot supply one.
4. **Data Sanitization:** Passwords, keys, and raw clinical document blobs are excluded from application logs.
