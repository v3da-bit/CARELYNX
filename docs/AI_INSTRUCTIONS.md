# CARELYNX — Master AI Instructions & Pre-Flight Manual

> **CRITICAL DIRECTIVE FOR ALL AI AGENTS & CODING ASSISTANTS:**  
> **READ THIS ENTIRE DOCUMENT BEFORE MODIFYING ANY FILE IN THIS REPOSITORY.**  
> Any AI assisting this project must remain aligned with the existing architecture and product vision. Do NOT introduce new concepts, unapproved architectural patterns, or out-of-scope features.

---

## 1. Project Identity & North Star Goal

- **Project:** CARELYNX
- **Primary Goal:** **Clearer Discharge Instructions** for patients and caregivers.
- **Core Value:** Transforming dense, fragmented healthcare discharge paperwork (summaries, prescriptions, lab sheets) into clear, evidence-linked, multilingual care plans, while exposing uncertainty and escalating ambiguous or conflicting cases to human review.

### The Golden Rule
> **"If the system cannot verify a statement directly from source document evidence, it MUST NOT present that statement as a verified fact."**

---

## 2. Strict Non-Goals (Boundaries You Must Not Cross)

Never propose, implement, or drift toward:
1. ❌ **Autonomous Medical Diagnosis:** Do not interpret lab results or symptoms as a disease diagnosis.
2. ❌ **Treatment Recommendations:** Do not suggest new drugs, therapies, or clinical interventions.
3. ❌ **Medication Dosage Modifications:** Never alter, recalculate, or suggest alternative drug dosages.
4. ❌ **Replacing Healthcare Professionals:** CARELYNX is an *information navigation* tool, not a doctor.
5. ❌ **Arbitrary Tie-Breaking:** If two documents conflict (e.g. follow-up dates differ), do NOT guess which one is "correct". Escalate to `CONFLICT_DETECTED` and human review.
6. ❌ **Hallucinated or Fabricated Fallbacks:** Never hardcode dummy clinical data as a fallback when document parsing fails. If an invalid or non-medical document is uploaded, fail gracefully with structured errors.
7. ❌ **Conceptual / Architectural Drift:** Do not attempt to turn this project into an EHR, a telemedicine app, a chatbot doctor, or rewrite the stack into alternative frameworks.

---

## 3. Mandatory Pre-Flight Reading Order

Before writing code or answering implementation prompts, review the following documents in order:

| Step | Document | Purpose |
|---|---|---|
| 1 | [`/docs/AI_INSTRUCTIONS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_INSTRUCTIONS.md) | This guide: rules, boundaries, and logging duties |
| 2 | [`/docs/TEAM.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/TEAM.md) | Team structure, roles, and instructions for team members |
| 3 | [`/docs/PRD.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/PRD.md) | Product vision, user personas, and MVP feature scope |
| 4 | [`/docs/SRS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/SRS.md) | Functional (FR) & Non-Functional (NFR) requirements, error codes |
| 5 | [`/docs/ARCHITECTURE.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/ARCHITECTURE.md) | System components, data flow, AMD ROCm integration, and DB schema |
| 6 | [`/docs/API_CONTRACTS.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/API_CONTRACTS.md) | Precise JSON request and response specifications |
| 7 | [`/docs/SAFETY.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/SAFETY.md) | Safety policies, evidence matching, and review triggers |
| 8 | [`/docs/DATABASE.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/DATABASE.md) | SQL tables, UUID keys, UTC timestamps, and migrations |
| 9 | [`/docs/AI_LOG.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_LOG.md) | Historical task logs & format for recording your completed work |

---

## 4. Working with the 3-Person Team

You are pairing with a human team of 3 developers:
1. **Frontend Lead (Dedicated Frontend Developer):**
   - Owns `apps/web/` (Next.js 16, React 19, TypeScript, Tailwind CSS).
   - *AI Instruction:* Always maintain pristine component hierarchy, responsive layouts, rich medical styling, and strict TypeScript types matching `lib/api.ts`. Do not install ad-hoc bloated libraries.
2. **Backend Lead (Systems & Data Engineer):**
   - Owns `apps/api/` (FastAPI, SQLAlchemy, Alembic, Storage, Security).
   - *AI Instruction:* Preserve SQLite/PostgreSQL compatibility. Ensure private storage of files. Enforce standard error contracts.
3. **AI & Safety Lead (Inference & QA Engineer):**
   - Owns `apps/api/app/ai/`, `apps/api/app/safety/`, and AMD ROCm integration.
   - *AI Instruction:* Keep inference behind the `InferenceProvider` interface. Enforce verbatim evidence matching and deterministic conflict detection.

---

## 5. Architectural & Technical Invariants

1. **Repository Layout:**
   - Web application: `apps/web/`
   - API backend: `apps/api/`
   - Documentation & specifications: `docs/`
2. **Evidence Linking Invariant:**
   - Every extracted medical fact must have an `evidence` record with `document_id`, `page_number`, `section`, and `snippet`.
   - The snippet **must literally appear** on the specified document page.
3. **Deterministic Safety Status Invariant:**
   - Do NOT let the LLM declare its own certainty or status. Status is computed deterministically in application code (`app/safety/`).
   - Allowed statuses: `VERIFIED`, `NEEDS_REVIEW`, `HUMAN_REQUIRED`, `CONFLICT_DETECTED`, `REJECTED`.
4. **Multilingual Invariant:**
   - Translation (`en`, `hi`, `gu`) must never alter drug names, dosages, dates, or dilute uncertainty indicators (e.g. "needs review" cannot become "verified").
5. **AMD Inference Path:**
   - Local development uses `rule_based` provider by default.
   - Production / GPU testing uses `openai_compatible` provider pointing to an AMD ROCm-hosted vLLM endpoint.

---

## 6. The AI Task Execution Loop

Follow this systematic loop for every coding task:

```text
1. REVIEW REQUIREMENTS
   - Re-check docs/PRD.md, SRS.md, and ARCHITECTURE.md for alignment.

2. PLAN MINIMAL & PRECISE EDITS
   - Plan exact file changes. Avoid touching unrelated files or overwriting existing patterns.

3. IMPLEMENT CODE
   - Maintain documentation integrity (preserve docstrings and comments).
   - Follow established conventions (FastAPI routers, Next.js components, Tailwind CSS).

4. VERIFY & TEST
   - Check API health (`/api/v1/health`).
   - Run type checks / tests when applicable.
   - Verify that servers run cleanly without unhandled exceptions.

5. LOG YOUR WORK
   - Immediately append a git-commit formatted log entry to docs/AI_LOG.md.
```

---

## 7. Mandatory Task Completion Logging

Upon completing ANY task, you **MUST** record your log in [`docs/AI_LOG.md`](file:///home/common/Documents/Carelynx/CARELYNX/docs/AI_LOG.md).

### Required Git Commit Format:
```text
commit <40-char-hex-hash or short-hash>
Author: <AI Agent Model Name> <<agent>@carelynx.local>
Date:   YYYY-MM-DD HH:MM:SS ±ZZZZ

    <type>(<scope>): <concise summary title>

    - Context / Problem addressed:
      Brief explanation of why this change was requested or needed.
    - Architectural decisions & changes made:
      Key technical decisions and specific logic implemented.
    - Files created / modified:
      List of relative file paths touched.
    - Verification & testing performed:
      Commands executed and validation results observed.
    - Alignment check:
      Confirmed compliance with docs/PRD.md and docs/SAFETY.md.
```

Adherence to this protocol is strictly required to ensure all team members and subsequent AI agents remain synchronized.
