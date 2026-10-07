# CARELYNX — Software Requirements Specification

## 1. Scope

This specification defines the technical requirements for CARELYNX MVP.

---

## 2. Functional Requirements

### FR-001 Document Upload
The system shall allow authenticated users to upload supported healthcare documents.

### FR-002 File Validation
The system shall reject unsupported file types and files exceeding configured limits.

### FR-003 Document Identification
The system shall assign a unique identifier to every uploaded document.

### FR-004 Text Extraction
The system shall extract machine-readable text where possible.

### FR-005 OCR
The system shall support OCR for image/scanned documents.

### FR-006 Page Preservation
The system shall preserve page-level location for extracted information.

### FR-007 Structured Extraction
The system shall transform source information into validated structured facts.

### FR-008 Evidence Metadata
Each document-derived fact shall contain source metadata.

### FR-009 Confidence
Each extracted fact shall have a system-generated confidence/status based on validation signals.

### FR-010 Uncertainty
The system shall expose uncertain results to users/reviewers.

### FR-011 Conflict Detection
The system shall identify conflicting values for relevant facts across documents.

### FR-012 Abstention
The system shall refuse to produce a definitive document-derived answer when evidence is insufficient.

### FR-013 Care Plan
The system shall generate a patient-readable organization of documented instructions and follow-ups.

### FR-014 Translation
The system shall translate supported patient-facing content into configured languages.

### FR-015 Human Review
The system shall create review cases based on configurable safety triggers.

### FR-016 Review Resolution
Authorized reviewers shall be able to approve, reject or resolve a review case.

### FR-017 Audit Trail
The system shall record relevant document processing, review and safety events.

### FR-018 AI Provider Abstraction
The system shall allow AI inference providers to be replaced without changing product-level business logic.

### FR-019 AMD Deployment
The inference layer shall support an AMD-compatible deployment path for the hackathon workload.

---

## 3. Non-Functional Requirements

### NFR-001 Security
Sensitive data shall be protected in transit and at rest.

### NFR-002 Privacy
Development/testing data shall be synthetic or appropriately de-identified.

### NFR-003 Reliability
Processing failures shall produce explicit errors rather than fabricated results.

### NFR-004 Observability
Important processing and review events shall be logged.

### NFR-005 Maintainability
Frontend, backend, AI and persistence layers shall have clear boundaries.

### NFR-006 Accessibility
Core patient workflows shall be keyboard-accessible and readable.

### NFR-007 Performance
The MVP should provide visible processing progress and avoid blocking the UI unnecessarily.

### NFR-008 Traceability
Patient-facing document-derived claims must be traceable to source evidence.

### NFR-009 Safety
The system shall not provide autonomous diagnosis or treatment recommendations.

---

## 4. API Requirements

Suggested endpoints:

```text
POST   /api/documents
GET    /api/documents/{id}
POST   /api/documents/{id}/process

GET    /api/cases/{id}/facts
GET    /api/facts/{id}/evidence

POST   /api/care-plans
GET    /api/care-plans/{id}

POST   /api/translations
GET    /api/reviews
POST   /api/reviews/{id}/resolve

GET    /api/audit/{case_id}
```

---

## 5. Data Validation

All external payloads must be schema validated.

Example fact:

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "fact_type": "follow_up_date",
  "value": "2026-10-14",
  "source_page": 7,
  "source_section": "Follow-up",
  "confidence": 0.98,
  "status": "VERIFIED"
}
```

Allowed statuses:

```text
VERIFIED
NEEDS_REVIEW
HUMAN_REQUIRED
CONFLICT_DETECTED
REJECTED
```

---

## 6. Safety Triggers

Create a review case when:
- OCR confidence is below configured threshold.
- Required source evidence is missing.
- Two documents conflict.
- A high-risk field is ambiguous.
- Translation changes/loses meaning according to validation checks.
- The model produces invalid structured output.
- A safety policy validator blocks an output.

---

## 7. Error Handling

Errors must be categorized:

```text
UPLOAD_ERROR
OCR_ERROR
PARSING_ERROR
MODEL_ERROR
VALIDATION_ERROR
EVIDENCE_ERROR
CONFLICT_ERROR
REVIEW_REQUIRED
AUTH_ERROR
INTERNAL_ERROR
```

The user-facing message should be understandable and must not expose secrets or internal stack traces.

---

## 8. Testing Requirements

### Unit tests
- File validation
- Schema validation
- Confidence/status mapping
- Conflict detection
- Safety policy checks

### Integration tests
- Upload → extraction
- Extraction → evidence
- Evidence → care plan
- Conflict → review case
- Translation → validation

### Evaluation tests
Use a fixed synthetic/de-identified benchmark.

Track:
- Precision
- Recall
- F1 where appropriate
- Evidence-link correctness
- Conflict detection
- Human-review routing
- Unsupported-claim rate

---

## 9. Acceptance Criteria

MVP is acceptable when:

1. A PDF/image can be uploaded.
2. Text can be extracted.
3. Relevant facts can be structured.
4. Facts contain source references.
5. Uncertain information is flagged.
6. Conflicting information triggers human review.
7. Patient-facing care plan is generated.
8. English/Hindi/Gujarati output works for the demo.
9. No autonomous diagnosis/treatment behavior exists.
10. AMD inference path is demonstrated.
11. Audit events are recorded.
12. Benchmark results are available.
