# CARELYNX — Mandatory AI Agent Rules

> **THIS FILE IS AUTO-LOADED BY ALL AI AGENTS OPERATING IN THIS REPOSITORY.**
> It is discovered automatically by Antigravity, Gemini, and any agent that
> respects the `.agents/AGENTS.md` convention.

---

## ⛔ MANDATORY PRE-FLIGHT GATE — NO EXCEPTIONS

**You are NOT permitted to write code, modify files, run commands, or propose
architectural changes until you have completed the full document reading
checklist below.**

Failure to read these documents results in:
- Misaligned implementations that contradict the established architecture.
- Safety violations (hallucinated clinical data, unauthorized medical advice).
- Wasted team effort undoing your changes.

---

## Required Reading Checklist (Execute in Order)

You must **actually read** (not skim, not assume) each of these documents
using `view_file` or equivalent before proceeding with any task:

| # | Document | What You Learn |
|---|---|---|
| 1 | `docs/AI_INSTRUCTIONS.md` | Your operating rules, safety boundaries, non-goals, and the task execution loop you must follow. |
| 2 | `docs/TEAM.md` | The 3-person team structure, who owns which domain, and specific instructions for your role. |
| 3 | `docs/PRD.md` | Product vision, user personas, MVP scope, and the features you are building. |
| 4 | `docs/SRS.md` | Functional requirements (FR-001 to FR-017), non-functional requirements, API specs, and error taxonomy. |
| 5 | `docs/ARCHITECTURE.md` | System architecture, component boundaries, AMD ROCm integration, and database entity relationships. |
| 6 | `docs/API_CONTRACTS.md` | Exact JSON request/response schemas for every REST endpoint. |
| 7 | `docs/SAFETY.md` | Verbatim evidence linking rules, conflict detection policy, OCR handling, and translation safety invariants. |
| 8 | `docs/DATABASE.md` | PostgreSQL/SQLite schema, UUID primary keys, UTC timestamps, and Alembic migration commands. |
| 9 | `docs/AI_LOG.md` | Historical task log — review what previous agents have done so you don't duplicate or contradict their work. |

---

## After Reading: Confirm Alignment

After completing the reading checklist, state clearly in your response:

> "I have reviewed the following CARELYNX documents: AI_INSTRUCTIONS.md,
> TEAM.md, PRD.md, SRS.md, ARCHITECTURE.md, API_CONTRACTS.md, SAFETY.md,
> DATABASE.md, AI_LOG.md. I confirm alignment with the established
> architecture and safety boundaries."

Only then may you proceed to implement the user's request.

---

## After Completing Work: Mandatory Logging

Upon finishing ANY task, you **MUST** append a git-commit formatted entry to
`docs/AI_LOG.md` following the schema defined in `docs/AI_INSTRUCTIONS.md`.

---

## Hard Constraints (Violations Are Unacceptable)

1. **No architectural drift.** Do not introduce new frameworks, rewrite the
   stack, or expand the product scope beyond what is documented.
2. **No hallucinated clinical data.** If extraction fails, return structured
   errors — never invent fake medical facts.
3. **No autonomous medical decisions.** CARELYNX navigates information; it
   does not diagnose, prescribe, or alter dosages.
4. **No silent failures.** Every processing error must be typed and traceable.
5. **No skipping the reading checklist.** This rule is non-negotiable.
