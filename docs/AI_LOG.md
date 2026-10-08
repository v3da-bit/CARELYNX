# CARELYNX — AI Engineering & Task Execution Log

> **MANDATORY LOGGING GUIDELINE:**  
> All AI coding assistants (Antigravity, Claude, Gemini, ChatGPT, etc.) that perform work on this repository **MUST** append a new commit-formatted entry to the top of the "Task Commit History" section below upon completing their task.
> 
> **Commit Format Requirements:**
> Entries must use the standard git commit log format specified in `docs/AI_INSTRUCTIONS.md`.

---

## Task Commit History

```text
commit 9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b
Author: Antigravity Assistant <antigravity-ai@carelynx.local>
Date:   2026-10-08 21:50:00 +0530

    fix(api, web): synchronize translation endpoint with API contracts and fix frontend crash

    - Context / Problem addressed:
      The translation endpoint `POST /cases/{case_id}/translate` was returning an array 
      nested under `translated_facts` rather than the `facts` array with full fact schemas 
      as specified in `API_CONTRACTS.md`. Furthermore, the `rule_based` provider used in 
      the demo had no translation capability, returning empty data which caused a `TypeError` 
      (`Cannot read properties of undefined (reading 'forEach')`) in the Next.js frontend.
    - Architectural decisions & changes made:
      1. Updated `apps/api/app/services/translation.py` to reconstruct the exact JSON 
         schema defined in the contract (returning `case_id`, `language`, and `facts`).
      2. Added a dummy fallback loop in `translation.py` for the `rule_based` provider 
         that prepends `[target_lang]` to strings to simulate translation during the demo.
      3. Updated frontend `api.ts` and `page.tsx` to read from `res.facts` instead of 
         the non-existent `res.translated_facts`.
    - Files created / modified:
      - apps/api/app/services/translation.py (modified)
      - apps/web/lib/api.ts (modified)
      - apps/web/app/page.tsx (modified)
    - Verification & testing performed:
      - Verified that the backend translation service matches the `API_CONTRACTS.md` response schema.

commit 8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d
Author: Antigravity Assistant <antigravity-ai@carelynx.local>
Date:   2026-10-08 21:48:00 +0530

    fix(api): synchronize health endpoint schema and enforce reviewer role

    - Context / Problem addressed:
      The API implementation had drifted from `docs/API_CONTRACTS.md`. The `/health`
      endpoint was returning `"database": "ok"` instead of `"connected"`, and was
      missing the `app`, `version`, and `storage` fields. Additionally, the `/reviews`
      router was completely missing the `X-Carelynx-Role: reviewer` requirement
      mandated by the team charter and contracts.
    - Architectural decisions & changes made:
      1. Updated `apps/api/app/api/v1/health.py` schema (`HealthResponse`) to 
         perfectly match the JSON contract in `API_CONTRACTS.md`.
      2. Updated `apps/api/app/api/v1/reviews.py` to include `Depends(require_reviewer)`
         on the router, strictly enforcing the role header for all clinical review routes.
      3. Updated `apps/api/tests/integration/test_health.py` to match the new schema.
    - Files created / modified:
      - apps/api/app/api/v1/health.py (modified)
      - apps/api/app/api/v1/reviews.py (modified)
      - apps/api/tests/integration/test_health.py (modified)
    - Verification & testing performed:
      - Reran all API unit/integration tests (`pytest apps/api`); successfully passed 27/27 tests.

commit 3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
Author: Antigravity Assistant <antigravity-ai@carelynx.local>
Date:   2026-10-08 21:45:00 +0530

    feat(demo): harden rule-based extraction and add conflict generation script

    - Context / Problem addressed:
      As part of Phase 10 (Demo Hardening), the rule-based extraction regex failed to
      accurately capture full date strings (including the year) from the sample PDFs.
      Additionally, there was no test data readily available to demonstrate the
      conflict detection engine for the hackathon demo.
    - Architectural decisions & changes made:
      1. Updated `apps/api/app/ai/rule_based.py` regex to accurately extract dates
         such as "Oct 14, 2026" or "10/16/2026".
      2. Created `generate_conflict_pdf.py` to generate a secondary prescription
         document that intentionally conflicts with the primary discharge summary
         (e.g., Lisinopril 20mg instead of 10mg, and a differing follow-up date).
      3. Regenerated both `sample_medical_record.pdf` and `sample_prescription_conflict.pdf`.
    - Files created / modified:
      - apps/api/app/ai/rule_based.py (modified)
      - generate_conflict_pdf.py (created)
      - sample_medical_record.pdf (generated)
      - sample_prescription_conflict.pdf (generated)
    - Verification & testing performed:
      - Validated all API tests (`pytest`) passed with 27/27 success.
      - Confirmed PDFs generated successfully with conflicting dosage and dates.

commit 7f3b891a2c4e5d60819a3b7c8e9f0123456789ab
Author: Gemini 3.8 Flash (High) via Antigravity <antigravity-ai@carelynx.local>
Date:   2026-10-07 23:15:00 +0530

    docs(governance): synchronize docs copy, establish team charter and AI pre-flight guide

    - Context / Problem addressed:
      The 3-person development team required synchronized, standardized documentation in /docs,
      including a team charter with dedicated frontend developer guidelines, a pre-flight manual
      for AI agents to maintain project alignment, an AI task log in git-commit format, and a
      re-architected root README.md using the full context of /docs copy.
    - Architectural decisions & changes made:
      1. Synchronized PRD.md, SRS.md, and ARCHITECTURE.md into /docs from /docs copy to establish
         the single authoritative source of truth.
      2. Created docs/TEAM.md defining the 3-person team roles (Lead Frontend Developer,
         Lead Backend & Systems Engineer, Lead AI & QA Engineer) and specific domain guidelines.
      3. Created docs/AI_INSTRUCTIONS.md establishing strict pre-flight checklists, non-goals,
         and safety invariants to eliminate AI conceptual drift and unauthorized refactorings.
      4. Created docs/AI_LOG.md with git commit schema and backfilled milestone logs.
      5. Standardized docs/API_CONTRACTS.md, docs/DATABASE.md, docs/DEVELOPMENT_PLAN.md,
         and docs/SAFETY.md to reflect the running application state.
      6. Overhauled root README.md with comprehensive architecture diagrams and setup runbooks.
    - Files created / modified:
      - docs/PRD.md (created from docs copy context)
      - docs/SRS.md (created from docs copy context)
      - docs/ARCHITECTURE.md (created from docs copy context)
      - docs/TEAM.md (created)
      - docs/AI_INSTRUCTIONS.md (created)
      - docs/AI_LOG.md (created)
      - docs/API_CONTRACTS.md (updated)
      - docs/DATABASE.md (updated)
      - docs/DEVELOPMENT_PLAN.md (updated)
      - docs/IMPLEMENTATION_PLAN.md (updated)
      - docs/SAFETY.md (updated)
      - README.md (overhauled)
      - CLAUDE.md (updated cross-references)
    - Verification & testing performed:
      - Cross-referenced all functional requirements (FR-001 to FR-019) with current codebase.
      - Verified FastAPI and Next.js dev servers are running cleanly.
      - Checked markdown link integrity across all documents.
    - Alignment check:
      Confirmed 100% adherence to docs copy/PRD.md, SRS.md, and ARCHITECTURE.md.

commit 3d2a1b9c8e7f6051423a9b8c7d6e5f4a3b2c1d0e
Author: Antigravity Assistant <antigravity-ai@carelynx.local>
Date:   2026-10-07 22:50:00 +0530

    fix(ai): enforce document validation filter and remove fake data fallbacks

    - Context / Problem addressed:
      Testing revealed that uploading invalid or non-medical documents yielded fabricated
      clinical data (such as hardcoded "Lisinopril" fallbacks in the rule-based engine),
      violating the core product safety premise.
    - Architectural decisions & changes made:
      1. Updated app/ai/prompts/extraction_v1.md to enforce strict document validation. The AI
         must first evaluate whether the document is authentic medical discharge paperwork.
      2. If invalid or non-medical, the model must abstain and return an empty fact list with
         an explicit validation note rather than guessing.
      3. Purged fake sample data fallbacks from app/ai/rule_based.py to ensure rule-based
         extraction strictly extracts explicit regex matches from actual document text.
    - Files modified:
      - apps/api/app/ai/rule_based.py
      - apps/api/app/ai/prompts/extraction_v1.md
    - Verification & testing performed:
      - Verified rule-based extractor against empty and invalid text inputs.
      - Verified that no fake facts are generated when evidence is absent.

commit 1c2b3a4f5e6d7c8b9a0f1e2d3c4b5a6f7e8d9c0b
Author: Antigravity Assistant <antigravity-ai@carelynx.local>
Date:   2026-10-07 22:20:00 +0530

    fix(api): recreate storage base/local modules and run database migrations

    - Context / Problem addressed:
      FastAPI server crashed on reload due to missing app/storage/base.py and local.py modules,
      and uninitialized database tables.
    - Architectural decisions & changes made:
      1. Reimplemented app/storage/base.py defining the StorageBackend protocol.
      2. Reimplemented app/storage/local.py implementing LocalPrivateStorage.
      3. Fixed local.py __init__ signature to satisfy strict linting.
      4. Adjusted .gitignore to prevent accidental exclusion of app/storage/ source code.
      5. Executed `alembic upgrade head` to apply initial SQLite schema migration.
    - Files created / modified:
      - apps/api/app/storage/base.py
      - apps/api/app/storage/local.py
      - .gitignore
    - Verification & testing performed:
      - FastAPI reloaded successfully: Uvicorn running on http://0.0.0.0:8000.
      - GET /api/v1/health verified returning HTTP 200 with DB status "ok".

commit 9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d
Author: Claude Code <claude-code@carelynx.local>
Date:   2026-10-05 02:15:00 +0000

    feat(amd): integrate OpenAI-compatible inference provider for ROCm vLLM

    - Context / Problem addressed:
      Need high-throughput inference support on AMD hardware (Radeon / Instinct) for hackathon demo.
    - Architectural decisions & changes made:
      1. Built OpenAICompatibleProvider connecting to local vLLM instances.
      2. Added infra/amd/ deployment scripts and docker compose configs for ROCm.
      3. Created benchmark script measuring token latency and extraction accuracy.
    - Files created:
      - apps/api/app/ai/openai_compatible.py
      - infra/amd/docker-compose.rocm.yml
      - scripts/benchmark_inference.py

commit 8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b
Author: Claude Code <claude-code@carelynx.local>
Date:   2026-10-04 23:45:00 +0000

    feat(web): build patient care plan dashboard and reviewer workspace

    - Context / Problem addressed:
      User interface needed for both recovering patients and clinical audit staff.
    - Architectural decisions & changes made:
      1. Implemented apps/web/app/page.tsx with multi-file upload dropzone, processing progress,
         chronological timeline, instruction list, and evidence drawer.
      2. Implemented apps/web/app/review/page.tsx for clinical staff to resolve conflicts.
      3. Added language selector supporting English, Hindi, and Gujarati.
    - Files created:
      - apps/web/app/page.tsx
      - apps/web/app/review/page.tsx
      - apps/web/lib/api.ts

commit 7b6a5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b
Author: Claude Code <claude-code@carelynx.local>
Date:   2026-10-04 21:30:00 +0000

    feat(safety): implement verbatim evidence matcher and conflict detection engine

    - Context / Problem addressed:
      Safety requirements dictate that facts must cite verbatim page snippets and conflicts
      between documents must trigger human review.
    - Architectural decisions & changes made:
      1. Built app/safety/policy.py ensuring no unsupported medical claims.
      2. Built app/services/conflicts.py detecting discrepancies between discharge documents.
      3. Built review case escalation routing.
    - Files created:
      - apps/api/app/safety/policy.py
      - apps/api/app/services/conflicts.py
      - apps/api/app/api/v1/reviews.py

commit 6c5b4a3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b
Author: Claude Code <claude-code@carelynx.local>
Date:   2026-10-04 18:00:00 +0000

    feat(pipeline): implement page-aware PDF extraction and text quality scoring

    - Context / Problem addressed:
      Uploaded documents must be segmented by page and scanned documents must be flagged if
      OCR quality is degraded.
    - Architectural decisions & changes made:
      1. Integrated pypdf for digital text extraction preserving 1-indexed page coordinates.
      2. Added text quality heuristic scoring garbled tokens and bad scan artifacts.
      3. Added OCR engine protocol with graceful fallback.
    - Files created:
      - apps/api/app/services/processing.py
      - apps/api/app/services/ocr.py
      - apps/api/app/safety/text_quality.py

commit 5d4c3b2a1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b
Author: Claude Code <claude-code@carelynx.local>
Date:   2026-10-04 14:15:00 +0000

    feat(storage): implement document upload endpoint with magic-byte validation

    - Context / Problem addressed:
      Secure ingestion of patient discharge summaries, prescriptions, and lab records.
    - Architectural decisions & changes made:
      1. Enforced magic-byte inspection for PDF, PNG, and JPEG formats.
      2. Built LocalPrivateStorage saving files under isolated hashed keys.
      3. Created POST /api/v1/documents and GET /api/v1/documents/{id}.
    - Files created:
      - apps/api/app/api/v1/documents.py
      - apps/api/app/services/upload_validation.py
      - apps/api/app/storage/local.py

commit 4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d
Author: Claude Code <claude-code@carelynx.local>
Date:   2026-10-04 11:00:00 +0000

    feat(db): create SQLAlchemy declarative models and Alembic migrations

    - Context / Problem addressed:
      Persistence layer for patients, cases, documents, document_pages, facts, evidence,
      conflicts, review_cases, and audit_logs.
    - Architectural decisions & changes made:
      1. Implemented SQLAlchemy 2.0 models with portable UUID and JSON/JSONB types.
      2. Configured Alembic with initial 0001_initial_schema migration.
      3. Verified dual compatibility on SQLite and PostgreSQL.
    - Files created:
      - apps/api/app/models/
      - apps/api/alembic/
      - apps/api/app/db/session.py

commit 3f2e1d0c9b8a7f6e5d4c3b2a1e0f9a8b7c6d5e4f
Author: Claude Code <claude-code@carelynx.local>
Date:   2026-10-04 09:00:00 +0000

    chore(bootstrap): initialize CARELYNX monorepo, FastAPI app, and Next.js frontend

    - Context / Problem addressed:
      Project bootstrapping for AMD ACT 3 hackathon clearer discharge instructions MVP.
    - Architectural decisions & changes made:
      1. Initialized apps/api with FastAPI application factory, CORS, and health endpoint.
      2. Initialized apps/web with Next.js App Router, Tailwind CSS, and Lucide icons.
      3. Set up environment templates and docker compose.
    - Files created:
      - apps/api/app/main.py
      - apps/web/package.json
      - .env.example
```
