# CARELYNX — Implementation Plan

> **Document Version:** 1.2.0  
> **Source of Truth:** `/docs/IMPLEMENTATION_PLAN.md`  
> **Status:** Synchronized with `/docs copy/` (PRD, SRS, ARCHITECTURE restored)  

---

## 1. Repository Assessment

### 1.1 Specification & Governance Baseline
All primary architectural specifications and engineering instructions are present and synchronized in `/docs`:

| Specification Document | Status | Location |
|---|---|---|
| `PRD.md` (Product Requirements Document) | ✅ Present | [`/docs/PRD.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/PRD.md) |
| `SRS.md` (Software Requirements Specification) | ✅ Present | [`/docs/SRS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/SRS.md) |
| `ARCHITECTURE.md` (System Architecture) | ✅ Present | [`/docs/ARCHITECTURE.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/ARCHITECTURE.md) |
| `TEAM.md` (Team Charter & Member Instructions) | ✅ Present | [`/docs/TEAM.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/TEAM.md) |
| `AI_INSTRUCTIONS.md` (AI Pre-Flight Guide) | ✅ Present | [`/docs/AI_INSTRUCTIONS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_INSTRUCTIONS.md) |
| `AI_LOG.md` (Git-Commit AI Execution Log) | ✅ Present | [`/docs/AI_LOG.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_LOG.md) |
| `SAFETY.md` (Clinical Safety Guardrails) | ✅ Present | [`/docs/SAFETY.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/SAFETY.md) |
| `API_CONTRACTS.md` (REST Interface Contracts) | ✅ Present | [`/docs/API_CONTRACTS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/API_CONTRACTS.md) |
| `DATABASE.md` (Database Schema Specification) | ✅ Present | [`/docs/DATABASE.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/DATABASE.md) |
| `DEVELOPMENT_PLAN.md` (Milestone Roadmap) | ✅ Present | [`/docs/DEVELOPMENT_PLAN.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/DEVELOPMENT_PLAN.md) |

### 1.2 Runtime Environment & Stack Assessment
| Tier | Technology | Local Dev Configuration | Production Configuration |
|---|---|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS | Running on port 3000 | Containerized Node / Vercel |
| Backend | FastAPI, Pydantic v2, Python 3.10+ | Running on port 8000 (Uvicorn) | Containerized ASGI cluster |
| Database | SQLAlchemy 2.0, Alembic | SQLite (`carelynx.db`) | PostgreSQL 16 (JSONB/TIMESTAMPTZ) |
| Storage | `StorageBackend` Protocol | `LocalPrivateStorage` | S3 / Supabase Private Bucket |
| AI Inference | `InferenceProvider` Protocol | `RuleBasedProvider` (regex/heuristics) | `OpenAICompatibleProvider` (vLLM ROCm) |

---

## 2. Core Architectural Decisions (ADR)

| # | Decision | Rationale |
|---|---|---|
| **D1** | **Monorepo Layout** (`apps/web`, `apps/api`, `docs`) | Enables tight coordination across the 3-person team while maintaining decoupled deployment boundaries. |
| **D2** | **Zero-Config Local Database with PostgreSQL Target** | SQLite fallback allows frictionless local development and test runs without requiring running Docker daemons, while models use portable SQLAlchemy types for clean PostgreSQL deployment. |
| **D3** | **Isolated Private Storage** (`LocalPrivateStorage`) | Medical documents must never be served statically from public web roots. Files are given non-predictable UUID keys and accessed exclusively through audited backend endpoints. |
| **D4** | **Inference Provider Abstraction** | Decouples product logic from model vendors. Enables local rule-based execution for testing and seamless connection to AMD ROCm vLLM instances via OpenAI-compatible endpoints. |
| **D5** | **Deterministic Safety Policies over LLM Self-Assessment** | The AI model is never trusted to calculate its own fact status or declare its own certainty. Fact status (`VERIFIED`, `NEEDS_REVIEW`, `CONFLICT_DETECTED`) is calculated deterministically in application code. |
| **D6** | **Verbatim Evidence Invariant** | Extracted snippets must match literal text extracted from the source page. Non-verbatim or unverified claims are blocked or routed to human review. |
| **D7** | **Dedicated Frontend Developer Ownership** | UI/UX in `apps/web/` is guided by a dedicated frontend engineer, ensuring polished medical styling, accessibility, and clean component architecture. |

---

## 3. Implementation Status Summary

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Repository Bootstrap (FastAPI + Next.js + DB session) | ✅ Complete |
| Phase 1 | Document Intake & Magic-Byte Validation | ✅ Complete |
| Phase 2 | Page-Aware PDF Extraction & Text Quality Scoring | ✅ Complete |
| Phase 3 | Structured Fact Extraction & Inference Engine | ✅ Complete |
| Phase 4 | Verbatim Evidence Matching & Conflict Detection | ✅ Complete |
| Phase 5 | Patient Care Plan Timeline & Evidence Drawer UI | ✅ Complete |
| Phase 6 | Multilingual Translation Engine (EN, HI, GU) | ✅ Complete |
| Phase 7 | Clinical Reviewer Workspace (`/review`) & Audit Log | ✅ Complete |
| Phase 8 | AMD ROCm Inference Deployment & Benchmark Scripts | ✅ Complete |
| Phase 9 | Synthetic Evaluation Datasets & Verification | ✅ Complete |
| Phase 10 | Documentation Synchronization & Team Alignment | ✅ Complete |
