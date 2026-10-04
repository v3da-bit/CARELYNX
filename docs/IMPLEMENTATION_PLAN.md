# CARELYNX — Implementation Plan

> Created by the engineering agent from `IMPLEMENTATION_PLAN_TEMPLATE.md` after inspecting the repository (2026-10-04).

## 1. Repository Assessment

### Existing stack
None. The repository contains **specification only** — no application code, no manifests, no git repo.

| Item | Found |
|---|---|
| `CLAUDE.md`, `README.md` | ✅ |
| `state.json`, `task_backlog.json` | ✅ |
| `docs/SAFETY.md`, `docs/API_CONTRACTS.md`, `docs/DATABASE.md`, `docs/DEVELOPMENT_PLAN.md` | ✅ |
| `docs/PRD.md`, `docs/SRS.md`, `docs/ARCHITECTURE.md` | ❌ **missing** (referenced by CLAUDE.md) |
| package manifests / Dockerfiles / tests | ❌ none |

### Local environment (measured)
| Tool | Status |
|---|---|
| Node | v24.14 / npm 11.9 |
| Python | 3.14.6 (only version available) |
| Docker | CLI 29.3 installed, **daemon not running** |
| PostgreSQL client | not installed |
| Tesseract / poppler | not installed |
| Hardware | Apple M4 — **no AMD GPU / ROCm locally** |

### Existing reusable components
None (greenfield).

### Existing problems / gaps
1. PRD/SRS/ARCHITECTURE are missing. Decisions below are derived from `CLAUDE.md` (which embeds architecture, stack and scope) plus the docs that exist. If those docs appear later, this plan must be reconciled.
2. No running Postgres locally → the app must still run (see decision D2).
3. No OCR engine locally → OCR adapter must degrade *explicitly*, never silently.
4. No AMD hardware locally → AMD provider is implemented behind the abstraction, but **no claim of AMD execution** is made until it actually runs on AMD.

---

## 2. Architecture Decision

Modular monolith, per CLAUDE.md §5.

```text
apps/web (Next.js + TS + Tailwind)  ──HTTP/JSON──▶  apps/api (FastAPI)
                                                     ├─ api/        thin routers
                                                     ├─ services/   business logic
                                                     ├─ repositories/ DB access
                                                     ├─ ai/         InferenceProvider + prompts
                                                     ├─ safety/     deterministic policy
                                                     ├─ storage/    private object storage abstraction
                                                     └─ models/ schemas/ db/
                                                          │
                                       PostgreSQL (prod/docker) │ SQLite (local fallback/tests)
```

### Decisions
| # | Decision | Rationale |
|---|---|---|
| D1 | Sync SQLAlchemy 2.x + sync FastAPI endpoints; AI provider methods are `async` per CLAUDE.md | Simplest reliable path; providers that do network I/O stay async. |
| D2 | Postgres is the target DB (docker-compose). `DATABASE_URL` defaults to local SQLite file when Postgres is unavailable. Models use portable types (`Uuid`, `JSON().with_variant(JSONB, "postgresql")`, tz-aware `DateTime`). | Keeps app runnable on this machine without Docker; production uses Postgres + JSONB per DATABASE.md. |
| D3 | Storage: `StorageBackend` protocol; `LocalPrivateStorage` (files outside web root, random keys, never served directly). S3/Supabase adapter is a drop-in later. | Private-by-default; no public URLs. |
| D4 | Processing runs synchronously inside `POST /documents/{id}/process` (status transitions persisted). A worker queue is not needed for the hackathon. | Demo reliability over premature scale. |
| D5 | PDF text via `pypdf` (page-aware). OCR via `OcrEngine` protocol: `TesseractOcr` (used only if installed) else `UnavailableOcr` → page marked `OCR_UNAVAILABLE` / needs review. | Explicit errors, no silent omission. |
| D6 | Text-quality confidence per page computed deterministically (garbled-char ratio, OCR-confusable tokens like `5OO`, `l0`) — used for Scenario B. | Bad OCR must be detectable even for text PDFs. |
| D7 | `InferenceProvider` protocol with: `RuleBasedProvider` (deterministic local extraction, default for dev/tests), `OpenAICompatibleProvider` (vLLM on ROCm exposes OpenAI-compatible API — **the AMD path**). Selected by `INFERENCE_PROVIDER` env. | No coupling to one model; honest AMD story. |
| D8 | All LLM output → Pydantic validation → safety validation → evidence validation (snippet must literally occur on the cited page) → persistence. | CLAUDE.md §13. |
| D9 | Fact status and confidence computed in application code (`safety/status.py`), not from LLM self-report. | CLAUDE.md §10. |
| D10 | Translation: `TranslationService` uses a curated phrase/template dictionary for UI + status strings (en/hi/gu) and passes patient-specific values (dates, drug names, doses) through **unchanged**. LLM translation optional behind the provider; output validated so numbers/dates/statuses are preserved. | Translation must not create new claims or drop uncertainty. |
| D11 | Auth for MVP: simple role header (`X-Carelynx-Role: patient|reviewer`) + documented as demo-only; reviewer endpoints require reviewer role. | Access-control boundary exists without building an IdP. |
| D12 | Frontend uses Tailwind (CLAUDE.md §4 explicitly specifies it). | Spec overrides generic default. |

---

## 3. Implementation Phases (mapped to backlog)

| Phase | Backlog | Output |
|---|---|---|
| 0 Plan | CLX-000 | this document |
| 1 Bootstrap | CLX-001 | FastAPI app + `/api/v1/health`, config, error contract, secure headers; Next.js shell; `.env.example`, `docker-compose.yml` |
| 2 DB | CLX-002 | SQLAlchemy models for all DATABASE.md tables, Alembic initial migration |
| 3 Upload | CLX-003 | `POST/GET /documents`, type sniffing (magic bytes), size limits, private storage |
| 4 Processing | CLX-004 | page-aware extraction, OCR adapter, page confidence, explicit errors |
| 5 Extraction | CLX-005 | `InferenceProvider`, fact schema, prompts, validation, persistence guard |
| 6 Evidence | CLX-006 | evidence verification, `GET /facts/{id}/evidence` |
| 7 Safety/Conflicts | CLX-007 | forbidden-content policy, status calc, conflict detection, review triggers |
| 8 Review | CLX-009 | review queue, detail, typed decisions, audit |
| 9 Care plan UI | CLX-008 | dashboard sections: Upload, Processing, Care Plan, Timeline, Documents, Evidence, Review Alerts, Language |
| 10 Multilingual | CLX-010 | en/hi/gu |
| 11 AMD | CLX-011 | OpenAI-compatible provider + `infra/amd` vLLM-ROCm deployment + benchmark script |
| 12 Evaluation | CLX-012 | synthetic dataset + metrics script |
| 13 Demo | CLX-013 | seeded scenarios A–D, clean-start runbook |

Order follows dependencies; CLX-009 (backend) is done before CLX-008 UI so the UI can show review alerts with real data.

---

## 4. Files to Create/Modify

```text
.gitignore  .env.example  docker-compose.yml  README.md (run instructions)
apps/api/
  pyproject.toml  requirements.txt  alembic.ini  alembic/env.py  alembic/versions/0001_initial.py
  app/main.py
  app/core/{config,errors,security,logging}.py
  app/db/{base,session}.py
  app/models/{patient,case,document,fact,review,audit}.py
  app/schemas/{common,document,fact,review,care_plan,translation}.py
  app/repositories/{documents,facts,reviews,audit}.py
  app/storage/{base,local}.py
  app/services/{documents,processing,extraction,evidence,conflicts,care_plan,review,translation,audit}.py
  app/ai/{provider,rule_based,openai_compatible,factory}.py  app/ai/prompts/extraction_v1.md
  app/safety/{policy,status,confidence,text_quality}.py
  app/api/v1/{health,documents,cases,facts,reviews}.py
  tests/{unit,integration}/...
apps/web/                  (create-next-app, TS, Tailwind, app router)
  app/page.tsx  app/cases/[id]/page.tsx  app/review/page.tsx
  components/*  lib/api.ts  lib/i18n.ts
tests/fixtures/            synthetic discharge PDFs (generated by script, no real PHI)
tests/evaluation/          dataset + run_eval.py
infra/amd/                 vLLM ROCm compose + README + benchmark
```

---

## 5. Dependency Plan

Backend: fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, alembic, psycopg[binary], python-multipart, pypdf, httpx; dev: pytest, ruff, mypy, reportlab (fixture generation only). Optional: pytesseract (only if Tesseract installed).

Frontend: next, react, typescript, tailwindcss. TanStack Query/Zod only if needed.

---

## 6. Testing Plan

- **Unit**: safety policy, text quality, status/confidence, evidence matching, conflict detection, translation preservation, upload validation.
- **Integration** (TestClient + SQLite temp DB): upload → process → facts → evidence; conflict → review; resolve → audit; care-plan only shows approved/verified content.
- **Safety tests**: the 8 cases in SAFETY.md §10, one test each, in `tests/unit/test_safety_cases.py`.
- **Evaluation**: `tests/evaluation/run_eval.py` over synthetic fixtures with expected facts.
- Tooling: `pytest`, `ruff check`, `mypy app` (backend); `npm run lint`, `tsc --noEmit`, `npm run build` (web).

---

## 7. Security/Safety Plan

- Upload: magic-byte type check (PDF/PNG/JPEG only), max size (`MAX_UPLOAD_MB`, default 15), filename sanitized, storage key random UUID.
- No public file URLs; originals served only through an authorized endpoint.
- Security headers middleware; generic error contract with `request_id`, no stack traces.
- Audit logs carry IDs/event types/counts — never document text.
- Safety policy enforced in code: forbidden-intent patterns (diagnosis, dose changes, substitution, triage), evidence requirement, conflict → never auto-resolved, high-risk fact types configurable.

---

## 8. AMD Integration Plan

- `OpenAICompatibleProvider` talks to any OpenAI-compatible endpoint. Target runtime: **vLLM ROCm image** on AMD Instinct (MI300X via AMD Developer Cloud) serving an open model (e.g. Llama-3.1-8B-Instruct / Qwen2.5-7B-Instruct).
- `infra/amd/` contains docker-compose for `rocm/vllm`, env, and a benchmark script recording latency/throughput + `rocm-smi` output.
- Until a run on AMD hardware is captured, docs state: *"AMD path implemented and deployable; not yet executed on AMD hardware."*

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| Python 3.14 wheel availability | Verified install; pin versions that install. |
| No Docker daemon/Postgres locally | SQLite fallback; Postgres via compose when daemon is up. Migrations tested on SQLite; JSONB variant for Postgres. |
| No Tesseract | Explicit `OCR_UNAVAILABLE` → HUMAN_REQUIRED path; demo uses text PDFs incl. synthetic "bad OCR" text. |
| No AMD hardware | Honest documentation; provider abstraction; remote AMD endpoint via env. |
| Missing PRD/SRS/ARCHITECTURE | Use CLAUDE.md as authority; record assumption. |
| Rule-based extractor coverage | Scoped to synthetic demo formats; LLM provider for general docs, still validated by same pipeline. |

---

## 10. First Task

CLX-001 — Bootstrap runnable application (FastAPI health endpoint, config, Next.js shell, env docs).

---

## 11. Decision Log (appended during implementation)

- 2026-10-04: Plan created. See D1–D12.
