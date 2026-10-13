# CARELYNX — API Contracts & Interface Specification

> **Document Version:** 2.0.0  
> **Source of Truth:** `/docs/API_CONTRACTS.md` — code (Pydantic schemas in `apps/api/app/schemas/`, TS types in `apps/web/lib/api.ts`) must match this file.  
> **Base Path:** `/api/v1`  
> **Protocol:** HTTP / JSON (multipart for uploads)  

---

## 1. General Principles

### 1.1 Access model (hackathon MVP)

| Caller | How it authenticates | What it can reach |
|---|---|---|
| Patient / caregiver | `X-Carelynx-Role: patient` (default when the header is absent) + the case UUID. | Case, documents, pages, file, facts, evidence, care plan of that case. |
| Clinical reviewer | `X-Carelynx-Role: reviewer`. | Everything above **plus** `/reviews/*` and `/cases/{id}/audit`. |

- Demo boundary only (decision D11): the header is not authentication. Production must replace it with real identity management.
- The reviewer identity recorded in `resolved_by` and the audit log is the `reviewer_id` sent in the resolve body.
- A non-reviewer role on a reviewer endpoint → `403 FORBIDDEN`; an unknown role value → `403 FORBIDDEN`.

### 1.2 Standard error contract

All errors use one shape. Stack traces and internal paths are never returned.

```json
{ "error": { "code": "UPLOAD_ERROR", "message": "File exceeds maximum upload size of 10MB.", "request_id": "a8098c1a-..." } }
```

| Code | HTTP | Raised when |
|---|---|---|
| `UPLOAD_ERROR` | 400 | Unsupported type / failed magic-byte check / empty file / > 10 MB |
| `VALIDATION_ERROR` | 422 | Request body/query fails validation (e.g. unknown `lang`) |
| `NOT_FOUND` | 404 | Unknown case / document / page / fact / review |
| `AUTH_ERROR` | 401 | Reserved for real authentication (not used by the demo role header) |
| `FORBIDDEN` | 403 | Authenticated but not allowed |
| `INVALID_STATE` | 409 | e.g. processing an already-processed document, resolving a resolved review |
| `CONFLICT_ERROR` | 409 | Review decision does not fit the review (e.g. `APPROVE` on a conflict review) |
| `REVIEW_REQUIRED` | 423 | Action blocked until clinical review is resolved |
| `OCR_ERROR` | 422 | Stored on a document as `error_code` when OCR crashed |
| `PARSING_ERROR` | 422 | Stored on a document as `error_code` when the PDF/image could not be parsed |
| `MODEL_ERROR` | 502 | Inference failed and no safe fallback produced a result |
| `EVIDENCE_ERROR` | 422 | Reserved: a fact's evidence cannot be verified |
| `INTERNAL_ERROR` | 500 | Anything unhandled (sanitized message) |

### 1.3 Enumerations

| Enum | Values |
|---|---|
| `FactStatus` | `VERIFIED`, `NEEDS_REVIEW`, `HUMAN_REQUIRED`, `CONFLICT_DETECTED`, `REJECTED` |
| `FactType` | `follow_up`, `medication`, `instruction`, `warning_sign`, `allergy`, `documented_condition`, `encounter_date` |
| `ProcessingStatus` | `UPLOADED`, `PROCESSING`, `PROCESSED`, `PROCESSED_WITH_WARNINGS`, `FAILED` |
| `ReviewReason` | `CONFLICT`, `LOW_TEXT_QUALITY`, `LOW_CONFIDENCE`, `MISSING_EVIDENCE`, `SAFETY_BLOCK`, `OCR_UNAVAILABLE`, `PROCESSING_FAILED` |
| `ReviewSeverity` | `LOW`, `MEDIUM`, `HIGH` |
| `ReviewDecision` | `APPROVE`, `REJECT`, `SELECT_SOURCE`, `CORRECT_VALUE` (see §6.3) |
| `Language` | `en`, `hi`, `gu`, `mr`, `ta`, `te` |
| `TranslationStatus` | `source` (lang=en), `translated`, `pending_review` (not VERIFIED → never sent for translation), `unavailable` (engine failed or safety check rejected output) |

---

## 2. Health

### `GET /health`
```json
{
  "status": "ok",
  "app": "carelynx-api",
  "version": "0.1.0",
  "database": "connected",
  "storage": "local_private",
  "inference_provider": "rule_based"
}
```
`status` is `ok` | `degraded`; `database` is `connected` | `unavailable`.

---

## 3. Cases

### `POST /cases` → `201`
```json
{ "id": "uuid", "status": "OPEN", "created_at": "2026-10-07T17:30:00Z" }
```

### `GET /cases/{case_id}` → `200`
```json
{
  "id": "uuid",
  "status": "OPEN",
  "created_at": "...",
  "documents": [ DocumentOut ],
  "counts": { "verified": 5, "needs_review": 1, "human_required": 0, "conflict_detected": 2, "rejected": 0, "open_reviews": 1 }
}
```

### `GET /cases/{case_id}/facts` → `200`  `FactWithEvidence[]`
All facts of the case (any status), each with its evidence.

### `GET /cases/{case_id}/care-plan?lang=en` → `200`
The patient-facing view. **All formatting, grouping, sorting and translation happen on the server**; the web client only renders it.

```json
{
  "case_id": "uuid",
  "language": "hi",
  "generated_at": "2026-10-07T17:40:00Z",
  "counts": { ...CaseCounts },
  "sections": {
    "follow_ups":      [ CarePlanItem ],
    "medications":     [ CarePlanItem ],
    "instructions":    [ CarePlanItem ],
    "warning_signs":   [ CarePlanItem ],
    "allergies":       [ CarePlanItem ],
    "conditions":      [ CarePlanItem ],
    "encounter_dates": [ CarePlanItem ]
  }
}
```

`CarePlanItem` = `FactWithEvidence` plus:
```json
{
  "display": {
    "title": "Follow-up appointment",
    "subtitle": "Cardiology · Dr. Sharma",
    "date": "2026-10-14"
  },
  "translation_status": "translated"
}
```
Rules:
- `REJECTED` facts are excluded. Every other status is included **with its status** so the UI can show ✓ / ⚠ / 🔴.
- `follow_ups` and `encounter_dates` are sorted by `display.date` ascending (undated last).
- `display` never invents data: a missing field is `null`, never a placeholder such as "Standard dose".
- Medication names, doses, dates and numbers are never translated (masked before translation, verified after).
- Only `VERIFIED` items are translated; others keep English text with `translation_status: "pending_review"`.
- `lang` outside `Language` → `422 VALIDATION_ERROR`.

### `GET /cases/{case_id}/fhir` → `200`
FHIR R4 `Bundle` (type `collection`) of **VERIFIED** `medication` facts as `MedicationStatement`s. Demo export; not a certified FHIR interface.

### `GET /cases/{case_id}/audit` → `200` (reviewer)
```json
[ { "id": "uuid", "event_type": "REVIEW_RESOLVED", "actor_type": "REVIEWER", "actor_id": null,
    "metadata": { "reviewer": "demo-reviewer", "decision": "SELECT_SOURCE" }, "created_at": "..." } ]
```
Newest first.

---

## 4. Documents

### `POST /documents` → `201`
`multipart/form-data`: `file` (PDF/PNG/JPEG ≤ 10 MB), `case_id` (optional; auto-creates a case).
```json
{ "id": "uuid", "case_id": "uuid", "filename": "discharge_summary.pdf", "status": "UPLOADED" }
```

### `POST /documents/{document_id}/process` → `200`
Runs page extraction/OCR → structured extraction → evidence verification → safety → conflict detection synchronously.
```json
{ "document_id": "uuid", "status": "PROCESSED", "error_code": null }
```
- OCR/parse failures do **not** raise: the document becomes `FAILED` with `error_code` (`OCR_ERROR` | `PARSING_ERROR`) and a `PROCESSING_FAILED` review case is opened.
- Processing a document that is `PROCESSING`, `PROCESSED` or `PROCESSED_WITH_WARNINGS` → `409 INVALID_STATE`. A `FAILED` document may be re-processed; its previous facts are removed first (no duplicates).

### `GET /documents/{document_id}` → `200`  `DocumentOut`
```json
{
  "id": "uuid", "case_id": "uuid", "filename": "discharge_summary.pdf", "mime_type": "application/pdf",
  "size_bytes": 48211, "sha256": "…", "page_count": 2, "processing_status": "PROCESSED",
  "document_kind": "discharge_summary", "error_code": null, "created_at": "...",
  "pages": [ { "page_number": 1, "extraction_method": "pdf_text", "text_quality": 0.98, "ocr_confidence": null, "quality_flags": [] } ]
}
```

### `GET /documents/{document_id}/pages/{page_number}` → `200`
```json
{ "id": "uuid", "document_id": "uuid", "page_number": 1, "extraction_method": "pdf_text",
  "text_quality": 0.98, "ocr_confidence": null, "quality_flags": [], "text": "PATIENT DISCHARGE SUMMARY\n..." }
```

### `GET /documents/{document_id}/file` → `200`
Original bytes (`application/pdf` | `image/png` | `image/jpeg`), `Cache-Control: no-store, private`. Every access is audited (`DOCUMENT_ACCESSED`).

---

## 5. Facts & Evidence

### `GET /facts/{fact_id}` → `200`  `FactResponse`
```json
{
  "id": "uuid", "case_id": "uuid", "fact_type": "medication",
  "value": { "name": "Aspirin", "strength": "75 mg", "frequency": "once daily" },
  "status": "VERIFIED", "confidence": 0.96, "status_reasons": [],
  "extracted_by": "rule_based", "human_verified": false, "created_at": "...", "updated_at": "..."
}
```
`extracted_by` is truthful provenance: `rule_based`, `openai_compat`, `rule_based (fallback from openai_compat)`, or `human_review`.

### `GET /facts/{fact_id}/evidence` → `200`  `EvidenceResponse[]`
```json
[ { "id": "uuid", "fact_id": "uuid", "document_id": "uuid", "document_filename": "prescription.pdf",
    "page_number": 2, "section": "Discharge Medications", "snippet": "Tab Aspirin 75mg OD after breakfast",
    "char_start": 120, "char_end": 155, "verified": true } ]
```

`FactWithEvidence` = `FactResponse` + `"evidence": EvidenceResponse[]`.

---

## 6. Clinical Review (reviewer key required)

### `GET /reviews?status=OPEN` → `200`  `ReviewCaseResponse[]`
`status` defaults to `OPEN`; `RESOLVED` lists resolved reviews. Newest first.
```json
{
  "id": "uuid", "case_id": "uuid", "reason": "Conflicting follow_up values across documents",
  "reason_code": "CONFLICT", "severity": "HIGH", "status": "OPEN",
  "fact_ids": ["uuid", "uuid"], "conflict_id": "uuid", "document_id": null,
  "recommended_action": "Confirm the correct follow-up date with the treating clinic.",
  "decision": null, "resolution": null, "resolved_by": null, "created_at": "...", "resolved_at": null
}
```

### `GET /reviews/{review_id}` → `200`  `ReviewDetail`
`ReviewCaseResponse` plus:
```json
{
  "facts": [ FactWithEvidence ],
  "conflict": { "id": "uuid", "fact_type": "follow_up", "conflict_data": { ... }, "status": "OPEN" },
  "documents": [ { "id": "uuid", "filename": "A_discharge_summary.pdf" } ]
}
```
`conflict` is `null` for non-conflict reviews. `documents` lists every document cited by the facts' evidence (plus `document_id` if set).

### `POST /reviews/{review_id}/resolve` → `200`  `ReviewCaseResponse`
```json
{
  "decision": "SELECT_SOURCE",
  "resolution_notes": "Confirmed with the cardiology clinic that 14 Oct is correct.",
  "winning_fact_id": "uuid",
  "corrected_value": null,
  "reviewer_id": "clinician-reviewer-1"
}
```

| Decision | Allowed on | Effect |
|---|---|---|
| `APPROVE` | non-conflict reviews | All `fact_ids` → `VERIFIED`, `human_verified=true` |
| `REJECT` | any review | All `fact_ids` → `REJECTED`, `human_verified=true` |
| `SELECT_SOURCE` | conflict reviews | `winning_fact_id` (must be in `fact_ids`) → `VERIFIED`; the others → `REJECTED` |
| `CORRECT_VALUE` | reviews whose `fact_ids` has exactly 1 fact, or with `winning_fact_id` naming one | That fact's `value` := `corrected_value` (object, required), `VERIFIED`, `extracted_by="human_review"`; other facts → `REJECTED` |

- `resolution_notes` is **required** (1–2000 chars). The client must never auto-fill it.
- A decision not allowed for the review → `409 CONFLICT_ERROR`; already resolved → `409 INVALID_STATE`.
- Resolving a conflict review also resolves the linked conflict. The `REVIEW_RESOLVED` audit row is written in the same transaction.
- `resolved_by` = `reviewer_id` from the body (required, 1–100 chars).
