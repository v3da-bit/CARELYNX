# CARELYNX — Development Plan

## Phase 0 — Repository Bootstrap

Goal:
Create a runnable monorepo/modular application.

Deliver:
- frontend
- FastAPI backend
- PostgreSQL
- environment configuration
- Docker/local startup
- health endpoint
- base UI

Exit criteria:
```text
Web starts
API starts
DB connects
Health check passes
```

---

## Phase 1 — Document Intake

Goal:
Allow users to upload healthcare documents.

Deliver:
- upload UI
- API endpoint
- validation
- storage abstraction
- document metadata
- processing status

Exit criteria:
A PDF/image can be uploaded and retrieved securely.

---

## Phase 2 — Processing

Goal:
Convert uploaded files into page-aware source content.

Deliver:
- PDF extraction
- OCR adapter
- page model
- document classification
- processing job/status

Exit criteria:
A test document produces page-level source text.

---

## Phase 3 — Structured Extraction

Goal:
Extract only explicitly supported information.

Deliver:
- Fact schema
- AI extraction provider
- structured output
- source references
- validation
- persistence

Exit criteria:
Known test document produces expected facts with evidence.

---

## Phase 4 — Evidence + Safety

Goal:
Make every output traceable and safe.

Deliver:
- evidence engine
- confidence/status calculation
- conflict detection
- unsupported claim blocking
- review triggers

Exit criteria:
Bad OCR and conflicting documents trigger appropriate review.

---

## Phase 5 — Patient Care Plan

Goal:
Turn validated facts into an understandable patient interface.

Deliver:
- timeline
- documented instructions
- follow-ups
- evidence drawer
- review alerts

Exit criteria:
A patient can understand what the source documents contain without needing to read every page.

---

## Phase 6 — Multilingual

Goal:
Support English, Hindi and Gujarati.

Deliver:
- translation service
- language selector
- source-preserving translation
- translation validation

Exit criteria:
Patient-facing content can switch languages without changing factual meaning/status.

---

## Phase 7 — Human Review

Goal:
Create a usable reviewer workflow.

Deliver:
- review queue
- case detail
- evidence inspection
- approve/reject
- resolution reason
- audit log

Exit criteria:
A reviewer can resolve an ambiguous case end-to-end.

---

## Phase 8 — AMD

Goal:
Run meaningful inference through AMD-compatible infrastructure.

Deliver:
- inference abstraction
- AMD provider
- ROCm-compatible runtime
- benchmark
- deployment documentation

Exit criteria:
The team can demonstrate the actual AI workload running through the AMD path.

---

## Phase 9 — Evaluation

Goal:
Prove impact.

Build synthetic/de-identified benchmark cases covering:
- clean PDFs
- scanned documents
- poor OCR
- missing data
- conflicting dates
- ambiguous fields
- multilingual content

Measure:
- extraction accuracy
- evidence accuracy
- conflict detection
- review routing
- unsupported claim rate
- latency
- time-to-information

---

## Phase 10 — Demo Hardening

Demo path:

```text
Open application
 ↓
Upload realistic discharge package
 ↓
Processing
 ↓
Care plan
 ↓
Click evidence
 ↓
Switch language
 ↓
Upload ambiguous document
 ↓
Safety warning
 ↓
Reviewer resolves
 ↓
Show metrics
 ↓
Show AMD architecture/workload
```

The demo must work from a clean environment using documented commands.
