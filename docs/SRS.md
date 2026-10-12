# CARELYNX — Software Requirements Specification (SRS)

> **Document Version:** 1.2.0  
> **Source of Truth:** `/docs/SRS.md` (the former `/docs copy/SRS.md` is merged in here)  
> **Target Audience:** Engineering Team (Frontend, Backend, AI/Inference) & AI Coding Assistants  

---

## 1. Scope & Objective

This document provides the formal software requirements for the CARELYNX application. It defines functional requirements (FR), non-functional requirements (NFR), interface specifications, data contracts, safety triggers, error categories, and acceptance criteria for the MVP.

---

## 2. Functional Requirements (FR)

### Document Ingestion & Validation
- **FR-001: Multi-Format Document Upload**  
  The system shall accept patient discharge documents in PDF, PNG, and JPEG formats via a multipart upload endpoint (`POST /api/v1/documents`).
- **FR-002: Strict File Validation & Magic-Byte Sniffing**  
  The system shall inspect magic bytes to verify file authenticity and reject any file that is corrupted, unsupported, or exceeds 10MB (`UPLOAD_ERROR`).
- **FR-003: Document Identification & Integrity**  
  The system shall assign a unique UUIDv4 to every uploaded document and compute an SHA-256 checksum for storage tracking.

### Text & Page Processing
- **FR-004: Page-Aware Digital Extraction**  
  The system shall parse digital PDF documents into distinct pages and maintain strict page numbering (1-indexed).
- **FR-005: OCR Fallback for Scans**  
  The system shall support an OCR pipeline (e.g., Tesseract or cloud OCR) to extract text from scanned PDFs or images. If OCR is unavailable, the page must be explicitly marked as `OCR_UNAVAILABLE`.
- **FR-006: Text Quality Scoring**  
  The system shall calculate an OCR confidence and text quality score based on garbled character ratios and confusable tokens.

### Structured Extraction & Evidence
- **FR-007: Structured Fact Extraction**  
  The system shall transform raw page text into structured entities: `follow_up`, `medication`, `instruction`, `warning_sign`, `allergy`, `documented_condition`, and `encounter_date`.
- **FR-008: Verbatim Evidence Verification**  
  Every extracted fact shall contain evidence metadata: `document_id`, `page_number`, `section`, and `snippet`. The system shall verify that the excerpt snippet exists verbatim on the source page.
- **FR-009: Deterministic Fact Status Calculation**  
  The system shall compute fact statuses in application logic (`VERIFIED`, `NEEDS_REVIEW`, `HUMAN_REQUIRED`, `CONFLICT_DETECTED`, `REJECTED`) rather than trusting model self-reports.
- **FR-010: Explicit Abstention**  
  The system shall refuse to produce a definitive medical fact when source evidence is missing, contradictory, or below confidence thresholds (`EVIDENCE_ERROR`).

### Clinical Safety & Conflict Management
- **FR-011: Multi-Document Conflict Detection**  
  The system shall automatically detect conflicting values across documents belonging to the same patient case (e.g., differing follow-up dates or contradictory medication dosages).
- **FR-012: Automatic Human Review Escalation**  
  The system shall immediately create a `review_case` whenever a conflict is detected, OCR confidence is low, or high-risk medical fields lack evidence.

### Patient Care Plan & Multilingual Support
- **FR-013: Plain-Language Care Plan Generation**  
  The system shall organize verified facts into an intuitive, chronological patient timeline and categorized care instructions.
- **FR-014: Source-Preserving Translation**  
  The system shall provide the care plan in English (`en`), Hindi (`hi`), Gujarati (`gu`), Marathi (`mr`), Tamil (`ta`), and Telugu (`te`). Only `VERIFIED` text is machine-translated; drug names, dosages, dates and numbers are masked before translation and verified afterwards, and any item failing that check is shown in English. Status labels and review warnings are never weakened.

### Clinical Review & Auditability
- **FR-015: Reviewer Decision Workflow**  
  Authorized reviewers shall be able to review flagged items, inspect side-by-side source evidence, and submit structured decisions (`APPROVE`, `REJECT`, `SELECT_SOURCE`, `CORRECT_VALUE`) with a mandatory written rationale. Reviewer endpoints require the demo role header `X-Carelynx-Role: reviewer`.
- **FR-016: Immutable Audit Logging**  
  The system shall record an audit log entry for every document processing stage, safety block, conflict detection, and human review resolution.
- **FR-017: AI Provider Abstraction**  
  The backend shall define an abstract `InferenceProvider` allowing transparent switching between rule-based local development, AMD ROCm vLLM server, and mock providers without code modifications.
- **FR-018: AMD Deployment Path**  
  The inference layer shall support an AMD-compatible (ROCm) deployment path for the hackathon workload, and results shall be labelled as AMD only when they actually ran on AMD hardware.
- **FR-019: Application-Level Confidence**  
  Each fact shall carry a system-computed confidence derived from validation signals (page quality, OCR confidence, evidence, legibility), never the model's self-reported confidence.

---

## 3. Non-Functional Requirements (NFR)

### NFR-001: Data Privacy & HIPAA / Healthcare Sensitivity
- Local development data must use synthetic or de-identified test records.
- Uploaded files must be stored in a private directory outside the web root (`LocalPrivateStorage` or encrypted S3 bucket).
- No sensitive patient identifiers, full medical records, or API credentials shall appear in standard logs.

### NFR-002: Reliability & Zero Hallucination Policy
- If an inference call fails or produces malformed JSON, the pipeline must fail gracefully with a typed error rather than inventing fallback medical values.

### NFR-003: Architectural Layering & Maintainability
- Strict separation of concerns:
  - Frontend: Next.js (App Router), TypeScript, Tailwind CSS.
  - Backend: FastAPI, Pydantic v2, SQLAlchemy 2.0.
  - Database: PostgreSQL (production) with SQLite zero-configuration local fallback.
  - AI Engine: Clean provider abstraction layer.

### NFR-004: Frontend Accessibility & Usability
- High contrast, legible typography (Tailwind theme), keyboard-accessible core patient workflows, modals and drawers, and clear status badges.
- Intuitive error banners explaining clinical uncertainty in non-alarming, constructive language.

### NFR-005: Performance & Response Times
- Document upload and ingestion must respond in $< 500\text{ms}$.
- Synchronous processing pipeline must complete within $< 5\text{s}$ for a standard 3-page discharge document on local hardware.
- The UI shall show visible upload/processing progress and must not block unnecessarily.

### NFR-006: Security
- Sensitive data shall be protected in transit (TLS via the deployment proxy) and at rest (target; see ARCHITECTURE §7).

### NFR-007: Observability
- Important processing, safety and review events shall be recorded (`audit_logs`).

### NFR-008: Traceability
- Every patient-facing, document-derived claim must be traceable to source evidence (document, page, snippet).

### NFR-009: Safety
- The system shall not provide autonomous diagnosis or treatment recommendations.

---

## 4. API Interface Requirements

All endpoints are prefixed with `/api/v1` and speak JSON. `docs/API_CONTRACTS.md` (v2.0) is the binding contract.
Access uses the demo role header `X-Carelynx-Role: patient|reviewer` (patient by default); reviewer endpoints
return `403 FORBIDDEN` for any other role. The reviewer identity is the `reviewer_id` in the resolve body.

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/health` | Service health, DB connectivity, storage, inference provider | Public |
| `POST` | `/cases` | Create an empty case | Patient |
| `GET` | `/cases/{id}` | Case, documents and fact/review counts | Patient (case UUID) |
| `GET` | `/cases/{id}/facts` | All facts of the case, each with evidence | Patient (case UUID) |
| `GET` | `/cases/{id}/care-plan?lang=` | Server-formatted care plan; REJECTED excluded, only VERIFIED translated (`en`, `hi`, `gu`, `mr`, `ta`, `te`) | Patient (case UUID) |
| `GET` | `/cases/{id}/fhir` | Demo FHIR R4 Bundle of VERIFIED medications | Patient (case UUID) |
| `GET` | `/cases/{id}/audit` | Case audit history, newest first | Reviewer (bearer) |
| `POST` | `/documents` | Upload multipart document (PDF/PNG/JPEG ≤ 10 MB) | Patient |
| `GET` | `/documents/{id}` | Document status & metadata | Patient (case UUID) |
| `POST` | `/documents/{id}/process` | Run OCR, extraction, evidence, safety and conflict pipeline | Patient |
| `GET` | `/documents/{id}/pages/{n}` | Page text for the evidence viewer | Patient (case UUID) |
| `GET` | `/documents/{id}/file` | Original file, private + audited | Patient / Reviewer |
| `GET` | `/facts/{id}` | One fact | Patient (case UUID) |
| `GET` | `/facts/{id}/evidence` | Evidence snippets and page citations | Patient (case UUID) |
| `GET` | `/reviews?status=OPEN\|RESOLVED` | Review queue | Reviewer (bearer) |
| `GET` | `/reviews/{id}` | Review with facts, evidence, conflict and documents | Reviewer (bearer) |
| `POST` | `/reviews/{id}/resolve` | Submit `APPROVE` / `REJECT` / `SELECT_SOURCE` / `CORRECT_VALUE` with required notes | Reviewer (bearer) |

---

## 5. Data Validation & Status Enums

### Fact Status Lifecycle
```text
                  ┌──────────────────────┐
                  │ Candidate Extracted  │
                  └──────────┬───────────┘
                             ▼
                 Verbatim Evidence Check
                  ┌──────────┴───────────┐
                  │                      │
             [Verified]             [Unverified]
                  │                      │
         Conflict Check                  ▼
         ┌────────┴────────┐      HUMAN_REQUIRED
         │                 │
    [No Conflict]      [Conflict]
         │                 │
         ▼                 ▼
      VERIFIED     CONFLICT_DETECTED
                           │
                           ▼
                  Human Review Queue
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          APPROVE_A    APPROVE_B      REJECT
```

---

## 6. Safety Triggers

A review case shall be created when:
- OCR confidence / page text quality is below the configured threshold (`SAFETY_MIN_PAGE_QUALITY`, default 0.85).
- Required source evidence is missing or does not match the page verbatim.
- Two documents conflict on the same fact.
- A high-risk field (medication, allergy, follow-up date, red-flag symptom) is not `VERIFIED`.
- The safety policy validator blocks an output.
- Processing fails (OCR/parse errors).

Invalid structured output from the LLM does not open a review: extraction falls back to the rule-based provider and the fallback is audited (ARCHITECTURE §3.4). Translation output that loses or alters a protected term or number is not shown; the English source is shown instead (SAFETY.md §5).

---

## 7. Error Handling Taxonomy

Every error uses `{"error": {"code", "message", "request_id"}}`; stack traces and paths are never returned.

| Error Code | HTTP Status | Meaning |
|---|---|---|
| `UPLOAD_ERROR` | 400 | Unsupported type, failed magic-byte check, empty file, or size > 10 MB |
| `VALIDATION_ERROR` | 422 | Request body/query fails validation (e.g. unknown `lang`, missing `resolution_notes`) |
| `NOT_FOUND` | 404 | Unknown case / document / page / fact / review |
| `AUTH_ERROR` | 401 | Reserved for real authentication (not used by the demo role header) |
| `FORBIDDEN` | 403 | Authenticated but not allowed |
| `INVALID_STATE` | 409 | e.g. processing an already-processed document, resolving a resolved review |
| `CONFLICT_ERROR` | 409 | Review decision does not fit the review (e.g. `APPROVE` on a conflict review) |
| `REVIEW_REQUIRED` | 423 | Action blocked until clinical review is resolved |
| `OCR_ERROR` | 422 | Stored on a document as `error_code` when OCR crashed (processing returns 200 `FAILED`) |
| `PARSING_ERROR` | 422 | Stored on a document as `error_code` when the PDF/image could not be parsed |
| `MODEL_ERROR` | 502 | Inference failed and no safe fallback produced a result |
| `EVIDENCE_ERROR` | 422 | Reserved: a fact's evidence cannot be verified |
| `INTERNAL_ERROR` | 500 | Anything unhandled (sanitized message) |

---

## 8. Testing Requirements

- **Unit:** file validation, schema validation, confidence/status mapping, evidence matching, conflict detection, safety policy, translation masking.
- **Integration:** upload → extraction, extraction → evidence, evidence → care plan, conflict → review case, review resolution → audit.
- **Evaluation:** fixed synthetic benchmark (`apps/api/demo/fixtures.py`, `scripts/evaluate_clinical.py`) tracking precision, recall, evidence-link correctness, conflict detection, human-review routing and unsupported-claim rate.

---

## 9. Acceptance Criteria (Definition of Done)

The CARELYNX MVP is accepted when all criteria below are verified:
1. Users can upload standard medical discharge PDFs and images via the frontend.
2. The backend extracts text and breaks documents into 1-indexed page records.
3. Extracted follow-up dates, medications, instructions, and warnings contain verified source citations.
4. Non-medical or unsupported assertions are flagged or rejected.
5. Injected conflicting documents automatically create a review case and prevent automatic display.
6. Clinical reviewers can inspect side-by-side evidence on the `/review` route and submit decisions.
7. Care plan timeline displays correctly in all six supported languages without fact degradation.
8. The system runs cleanly with zero cloud lock-in via SQLite/FastAPI/Next.js.
9. No autonomous diagnosis or treatment behaviour exists.
10. The AMD inference path is demonstrated (pending a GPU run — CLX-020).
11. Audit events are recorded.
12. Benchmark results are available.
