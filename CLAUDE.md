# CARELYNX — Claude Code Master Engineering Instruction

> This file is the primary instruction for the coding agent. Read it before changing any file.

---

# ⛔ MANDATORY PRE-FLIGHT READING GATE — EXECUTE BEFORE ALL ELSE

**YOU MUST NOT write any code, modify any file, run any command, or propose any
architectural change until you have read ALL of the following documents using
your file-reading tool.**

This is a hard prerequisite. Skipping it leads to misaligned implementations,
safety violations, and wasted team effort.

## Required Reading (in order):

1. `docs/AI_INSTRUCTIONS.md` — Operating rules, safety boundaries, non-goals, task execution loop.
2. `docs/TEAM.md` — 3-person team structure, domain ownership, member-specific instructions.
3. `docs/PRD.md` — Product vision, user personas, MVP scope, strict non-goals.
4. `docs/SRS.md` — Functional & non-functional requirements, error taxonomy.
5. `docs/ARCHITECTURE.md` — System components, data flow, AMD ROCm integration, DB schema.
6. `docs/API_CONTRACTS.md` — REST endpoint JSON contracts.
7. `docs/SAFETY.md` — Evidence linking, conflict triggers, OCR handling, translation safety.
8. `docs/DATABASE.md` — Table schemas, UUID keys, UTC timestamps, migrations.
9. `docs/AI_LOG.md` — Historical task log (review what previous agents did).
10. `task_backlog.json` — Current task queue and statuses.
11. `state.json` — Current project state and milestone tracker.

## After reading, confirm alignment:

> "I have reviewed all required CARELYNX documents and confirm alignment with
> the established architecture and safety boundaries."

## After completing work:

Append a git-commit formatted log entry to `docs/AI_LOG.md` (see format in
`docs/AI_INSTRUCTIONS.md`).

---
## 0. Mission

You are the primary autonomous software engineer for **CARELYNX**, an AMD ACT 3 hackathon project.

Build a production-quality hackathon MVP for:

> **Clearer discharge instructions**

CARELYNX processes healthcare discharge documents and converts them into clear, evidence-linked, multilingual patient information while making uncertainty visible and routing ambiguous/high-risk cases to human review.

### Core product promise

**If the system cannot support a medical statement from source evidence, it must not present that statement as fact.**

CARELYNX is an information-navigation and communication product. It is **not** a diagnosis engine, treatment recommender, medication-adjustment engine, or autonomous medical decision-maker.

---

# 1. How You Must Work

## First response / first execution

Before implementing features:

1. Inspect the existing repository.
2. Inspect package manifests, source tree, environment files, Docker files and existing tests.
3. Determine whether code already exists.
4. Do not overwrite useful existing work.
5. Read:
   - `docs/AI_INSTRUCTIONS.md`
   - `docs/TEAM.md`
   - `docs/PRD.md`
   - `docs/SRS.md`
   - `docs/ARCHITECTURE.md`
   - `docs/SAFETY.md`
   - `docs/API_CONTRACTS.md`
   - `docs/DATABASE.md`
   - `docs/DEVELOPMENT_PLAN.md`
   - `docs/AI_LOG.md`
   - `task_backlog.json`
   - `state.json`
6. Create/update `docs/IMPLEMENTATION_PLAN.md` with:
   - repository assessment
   - architecture decision
   - implementation phases
   - exact files/modules to create/change
   - dependencies
   - testing strategy
   - risks/blockers
7. Then start executing the highest-priority unblocked task.

Do not spend the entire session writing plans without implementing.

---

# 2. Execution Loop

For every task:

```text
READ
 ↓
UNDERSTAND
 ↓
PLAN SMALL CHANGE
 ↓
IMPLEMENT
 ↓
TEST
 ↓
SECURITY/SAFETY CHECK
 ↓
UPDATE DOCUMENTATION
 ↓
UPDATE state.json
 ↓
MOVE TO NEXT TASK
```

Work on **one logical task at a time**.

Do not mark a task complete unless its acceptance criteria are satisfied.

If blocked:
- Record the blocker.
- Do not fabricate a workaround that violates safety or architecture.
- Continue with another independent task when possible.

---

# 3. Product Scope

## MVP

The MVP is:

```text
Patient/caregiver
      ↓
Upload discharge documents
      ↓
PDF/image processing
      ↓
OCR/text extraction
      ↓
Structured fact extraction
      ↓
Evidence linking
      ↓
Uncertainty + conflict detection
      ↓
Clear patient care plan
      ↓
English/Hindi/Gujarati
      ↓
Human review for flagged cases
```

## Primary feature

**Clearer discharge instructions**

## Secondary features

- Healthcare document processing
- Medical record summarization
- Care navigation
- Multilingual patient communication

---

# 4. Technical Stack — Default Decisions

Unless the existing repository has a strong reason to differ, use:

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Accessible component primitives
- TanStack Query for server-state management where useful
- Zod for client-side validation where useful

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- PostgreSQL

## Storage

- S3-compatible object storage
- Supabase Storage is acceptable for the hackathon

## Database

- PostgreSQL
- UUID primary keys
- JSONB for flexible AI/evidence metadata
- UTC timestamps

## AI

Create an internal provider abstraction:

```python
class InferenceProvider(Protocol):
    async def generate_structured(...): ...
    async def generate_text(...): ...
```

Do not couple business logic directly to a single model provider.

## AMD

AMD must power a meaningful AI workload.

Preferred architecture:

```text
FastAPI
  ↓
AI Service
  ↓
InferenceProvider
  ↓
AMD GPU / ROCm runtime
  ↓
LLM
```

Use an AMD-compatible inference stack available in the actual hackathon environment. Candidates include ROCm-compatible PyTorch, vLLM, ONNX Runtime or another validated runtime.

Do not fake AMD integration.

If AMD hardware/runtime is unavailable locally:
- Implement the provider interface.
- Implement a local/mock provider for development.
- Document the exact AMD deployment path.
- Do not claim the workload ran on AMD unless it actually did.

---

# 5. Repository Structure

Use this target structure unless the existing repository requires adaptation:

```text
carelynx/
├── CLAUDE.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── task_backlog.json
├── state.json
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── hooks/
│   │   └── tests/
│   │
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── core/
│       │   ├── db/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── repositories/
│       │   ├── services/
│       │   ├── ai/
│       │   ├── safety/
│       │   ├── workers/
│       │   └── main.py
│       └── tests/
│
├── packages/
│   └── shared/
│       └── schemas/
│
├── infra/
│   ├── docker/
│   └── amd/
│
├── tests/
│   ├── fixtures/
│   ├── integration/
│   └── evaluation/
│
└── docs/
    ├── PRD.md
    ├── SRS.md
    ├── ARCHITECTURE.md
    ├── SAFETY.md
    ├── API_CONTRACTS.md
    ├── DATABASE.md
    ├── DEVELOPMENT_PLAN.md
    └── IMPLEMENTATION_PLAN.md
```

Do not create unnecessary microservices for the hackathon. Start as a modular monolith with clear boundaries.

---

# 6. Architectural Principles

## Evidence first

Every document-derived fact must have evidence.

Minimum:

```json
{
  "document_id": "uuid",
  "page_number": 7,
  "source_text": "..."
}
```

## Abstention first

When evidence is weak:

```text
Do not guess.
Do not silently omit.
Flag it.
```

## Deterministic validation around probabilistic AI

LLMs extract information.

Application code validates:
- schema
- source references
- conflicts
- required fields
- safety policy

## Human-in-the-loop

Humans resolve:
- conflicting medical facts
- low-confidence important fields
- unsupported/high-risk content
- ambiguous medication information
- safety-policy escalations

---

# 7. Safety Rules — ABSOLUTE

Never implement:

- diagnosis
- disease prediction presented as diagnosis
- treatment recommendation
- medication dose modification
- medication substitution
- emergency triage decisions
- clinical prioritization presented as medical advice
- unsupported symptom interpretation
- autonomous medical decisions

Never generate:

> "You should increase your dose."

Instead:

> "The uploaded document contains the following medication instruction: ..."

If the document cannot be reliably interpreted:

> "This information could not be reliably extracted. Human verification is required."

---

# 8. Source-of-Truth Hierarchy

For document-derived patient information:

```text
1. Human-approved source fact
2. Direct source document evidence
3. Validated structured extraction
4. AI-generated explanation grounded in source
5. Never unsupported model knowledge for patient-specific facts
```

The model must not fill missing patient-specific information using general medical knowledge.

---

# 9. Fact Status Model

Use these states:

```text
VERIFIED
NEEDS_REVIEW
HUMAN_REQUIRED
CONFLICT_DETECTED
REJECTED
```

### VERIFIED

Directly supported by evidence and validation checks.

### NEEDS_REVIEW

Potentially correct but not sufficiently reliable.

### HUMAN_REQUIRED

System must not present the item as actionable until reviewed.

### CONFLICT_DETECTED

Multiple sources disagree.

### REJECTED

Invalid or unsafe output.

---

# 10. Confidence

Do not blindly trust an LLM's self-reported confidence.

Create application-level confidence from signals such as:

```text
OCR confidence
+
schema validity
+
evidence presence
+
source matching
+
cross-document consistency
+
domain-specific validation
```

Keep confidence as a decision-support signal, not a guarantee.

---

# 11. Critical Demo Scenarios

The implementation MUST support these demo cases.

## Scenario A — Normal

Input:
- discharge summary
- prescription
- follow-up document

Output:
- care plan
- follow-up date
- documented instructions
- evidence references

## Scenario B — Bad OCR

Input contains intentionally ambiguous text.

Output:

```text
NEEDS REVIEW

The system could not reliably read this field.

CARELYNX will not guess.
```

## Scenario C — Conflicting documents

Example:

```text
Document A: Follow-up 14 Oct
Document B: Follow-up 16 Oct
```

Output:

```text
CONFLICT DETECTED

Human verification required.
```

The system must not automatically select one.

## Scenario D — Multilingual

Generate English → Hindi/Gujarati patient-facing communication.

Translation must preserve uncertainty and source meaning.

---

# 12. UX Requirements

The patient dashboard must make the following immediately understandable:

```text
What do my documents say?
Where did this information come from?
What needs my attention?
What is uncertain?
Who needs to review something?
```

Primary UI sections:

1. Upload
2. Processing
3. Care Plan
4. Timeline
5. Documents
6. Evidence
7. Review Alerts
8. Language

Use visual status:

```text
✓ Verified
⚠ Needs review
🔴 Human review required
```

Do not use visual design that implies medical authority or certainty.

---

# 13. API Principles

API contracts must use typed Pydantic models.

Never return raw LLM output directly to the frontend.

Flow:

```text
LLM
 ↓
Pydantic validation
 ↓
Safety validation
 ↓
Evidence validation
 ↓
Persistence
 ↓
API response
```

---

# 14. Testing Requirements

Every meaningful backend feature needs tests.

Minimum:

### Unit
- validation
- evidence matching
- conflict detection
- status calculation
- safety rules

### Integration
- upload → process
- process → facts
- facts → evidence
- conflict → review
- approved facts → care plan

### Evaluation
Maintain a fixed synthetic/de-identified dataset.

Measure:
- extraction precision/recall
- evidence correctness
- conflict detection
- escalation correctness
- unsupported claim rate
- latency
- time-to-information

---

# 15. Security Requirements

Never commit:
- API keys
- credentials
- patient documents
- private tokens
- database passwords

Use `.env.example`.

Production-like defaults:
- secure headers
- input validation
- file type validation
- upload size limits
- access control
- signed/private document URLs
- audit logging
- minimal PII retention

---

# 16. Code Quality

Prefer:

```text
services/
repositories/
schemas/
models/
ai/
safety/
```

Avoid:
- giant route handlers
- business logic in React components
- business logic embedded in prompts
- duplicated validation
- magic strings
- untyped dictionaries everywhere

Every major domain should have a clear service boundary.

---

# 17. Prompt Engineering Rules

Prompts are versioned code.

Store important prompts under:

```text
apps/api/app/ai/prompts/
```

Each prompt must state:
- role
- task
- allowed information
- forbidden behavior
- output schema
- evidence requirement
- abstention behavior

Never rely on a prompt alone for safety.

Safety must also be enforced in application code.

---

# 18. Agent Behavior

When implementing:
- Prefer small commits/changes.
- Do not refactor unrelated code.
- Do not install a dependency if standard library/current stack is sufficient.
- Do not replace working infrastructure without reason.
- Keep the application runnable after each milestone.
- Run relevant tests after changes.
- Fix failures before moving on.

When uncertain between two implementation choices:
1. Prefer the simpler one.
2. Prefer maintainability.
3. Prefer explicit safety.
4. Prefer hackathon-demo reliability over premature scale.

---

# 19. Completion Standard

The project is not "done" when the UI looks good.

MVP is done when:

- document upload works
- document processing works
- facts are structured
- facts have evidence
- uncertainty is visible
- conflicts are detected
- human review works
- patient care plan works
- English/Hindi/Gujarati works
- safety rules are tested
- AMD inference path is integrated or demonstrably deployable
- benchmark is run
- demo can be executed from clean startup instructions

---

# 20. What To Do Now

Immediately:

1. Inspect repository.
2. Read all project documents.
3. Create `docs/IMPLEMENTATION_PLAN.md`.
4. Update `task_backlog.json` if repository reality requires changes.
5. Update `state.json`.
6. Begin the first P0 task.
7. Keep the project runnable.
8. Report:
   - what you found
   - what you changed
   - tests run
   - current task
   - next task
