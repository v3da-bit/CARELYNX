# CARELYNX — API Contracts & Interface Specification

> **Document Version:** 1.1.0  
> **Source of Truth:** `/docs/API_CONTRACTS.md`  
> **Base Path:** `/api/v1`  
> **Protocol:** HTTPS / JSON (Multipart for uploads)  

---

## 1. General Principles & Headers

### Headers
| Header | Type | Description |
|---|---|---|
| `Content-Type` | string | `application/json` (or `multipart/form-data` for file uploads) |
| `X-Carelynx-Role` | string | `patient` (default) or `reviewer`. Required for clinical review endpoints |
| `X-Request-ID` | string | Optional client-generated or server-reflected tracing UUID |

### Standard Error Contract
All API errors return a uniform JSON schema. Raw stack traces are never exposed to clients.

```json
{
  "error": {
    "code": "UPLOAD_ERROR",
    "message": "File exceeds maximum upload size of 10MB.",
    "request_id": "a8098c1a-f703-4c9b-864a-2512f55e0031"
  }
}
```

Standard Error Codes:
- `UPLOAD_ERROR` (400)
- `VALIDATION_ERROR` (422)
- `NOT_FOUND` (404)
- `OCR_ERROR` (422)
- `EVIDENCE_ERROR` (422)
- `CONFLICT_ERROR` (409)
- `REVIEW_REQUIRED` (423)
- `UNAUTHORIZED` / `FORBIDDEN` (401 / 403)
- `INTERNAL_ERROR` (500)

---

## 2. Health & System Endpoints

### `GET /health`
Returns system liveness, database status, and storage status.

**Response `200 OK`:**
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

---

## 3. Cases Endpoints (`/cases`)

### `POST /cases`
Initializes a new patient encounter case.

**Response `201 Created`:**
```json
{
  "id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
  "patient_id": null,
  "status": "OPEN",
  "created_at": "2026-10-07T17:30:00Z"
}
```

---

### `GET /cases/{case_id}`
Retrieves case overview, attached documents, and aggregated fact status counts.

**Response `200 OK`:**
```json
{
  "id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
  "status": "OPEN",
  "created_at": "2026-10-07T17:30:00Z",
  "documents": [
    {
      "id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
      "filename": "discharge_summary.pdf",
      "mime_type": "application/pdf",
      "page_count": 2,
      "processing_status": "PROCESSED",
      "created_at": "2026-10-07T17:31:00Z"
    }
  ],
  "counts": {
    "verified": 5,
    "needs_review": 1,
    "human_required": 0,
    "conflict_detected": 1,
    "rejected": 0,
    "open_reviews": 1
  }
}
```

---

### `GET /cases/{case_id}/facts`
Retrieves all structured facts extracted from documents belonging to the case.

**Response `200 OK`:**
```json
[
  {
    "id": "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
    "case_id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
    "fact_type": "follow_up_date",
    "value": {
      "date": "2026-10-14",
      "provider": "Dr. Sharma",
      "department": "Cardiology",
      "notes": "Follow up in OPD room 302"
    },
    "status": "VERIFIED",
    "confidence": 0.98,
    "human_verified": false,
    "status_reasons": ["Verbatim evidence verified on page 2"],
    "created_at": "2026-10-07T17:32:00Z"
  }
]
```

---

### `POST /cases/{case_id}/translate?target_lang={lang}`
Translates verified case facts and instructions into the target language (`en`, `hi`, `gu`).

**Query Parameters:**
- `target_lang`: `hi` (Hindi) | `gu` (Gujarati) | `en` (English)

**Response `200 OK`:**
```json
{
  "case_id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
  "language": "hi",
  "facts": [
    {
      "id": "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
      "fact_type": "follow_up_date",
      "translated_value": {
        "date": "2026-10-14",
        "provider": "डॉ. शर्मा",
        "department": "कार्डियोलॉजी",
        "notes": "ओपीडी कक्ष 302 में फॉलो-अप"
      },
      "status": "VERIFIED"
    }
  ]
}
```

---

## 4. Document Endpoints (`/documents`)

### `POST /documents`
Uploads a document (`PDF`, `PNG`, `JPEG`). Validates magic bytes and stores file in private storage.

**Request:** `multipart/form-data`
- `file`: binary file contents
- `case_id`: UUID string (optional; auto-creates if omitted)

**Response `201 Created`:**
```json
{
  "id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "case_id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
  "filename": "discharge_summary.pdf",
  "status": "UPLOADED"
}
```

---

### `POST /documents/{document_id}/process`
Runs the document extraction, OCR, structured fact parsing, verbatim evidence check, and safety policy pipeline synchronously.

**Response `200 OK`:**
```json
{
  "document_id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "status": "PROCESSED"
}
```

---

### `GET /documents/{document_id}`
Returns document metadata and status.

**Response `200 OK`:**
```json
{
  "id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "case_id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
  "filename": "discharge_summary.pdf",
  "mime_type": "application/pdf",
  "page_count": 2,
  "processing_status": "PROCESSED",
  "created_at": "2026-10-07T17:31:00Z"
}
```

---

### `GET /documents/{document_id}/pages/{page_number}`
Retrieves extracted text and OCR quality confidence score for an individual page (1-indexed).

**Response `200 OK`:**
```json
{
  "id": "8b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
  "document_id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "page_number": 1,
  "text": "PATIENT DISCHARGE SUMMARY\nDiagnosis: Acute Coronary Syndrome...",
  "ocr_confidence": 0.99
}
```

---

### `GET /documents/{document_id}/file`
Securely streams original document file bytes. Requires authorization and records an audit log.

**Headers:**
- `X-Carelynx-Role`: `patient` or `reviewer`

**Response `200 OK`:**
- Binary stream (`application/pdf`, `image/png`, or `image/jpeg`)
- Header: `Cache-Control: no-store, private`

---

## 5. Facts & Evidence Endpoints (`/facts`)

### `GET /facts/{fact_id}`
Retrieves a specific fact by UUID.

**Response `200 OK`:**
```json
{
  "id": "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "case_id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
  "fact_type": "medication",
  "value": {
    "drug_name": "Aspirin",
    "dosage": "75mg",
    "frequency": "Once daily",
    "duration": "Ongoing"
  },
  "status": "VERIFIED",
  "confidence": 0.96,
  "human_verified": false,
  "status_reasons": []
}
```

---

### `GET /facts/{fact_id}/evidence`
Retrieves line-by-line evidence citations supporting a specific fact.

**Response `200 OK`:**
```json
[
  {
    "id": "9c0d1e2f-3a4b-5c6d-7e8f-9a0b1c2d3e4f",
    "fact_id": "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
    "document_id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
    "page_number": 2,
    "section": "Discharge Medications",
    "snippet": "Tab Aspirin 75mg OD after breakfast"
  }
]
```

---

## 6. Clinical Review Endpoints (`/reviews`)

Requires header: `X-Carelynx-Role: reviewer`

### `GET /reviews`
Lists all open review cases requiring clinical resolution.

**Response `200 OK`:**
```json
[
  {
    "id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "case_id": "e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f",
    "reason": "Conflicting follow-up dates between Discharge Summary and Prescription",
    "severity": "HIGH",
    "status": "OPEN",
    "fact_ids": [
      "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
      "4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a"
    ],
    "conflict_id": "5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b",
    "created_at": "2026-10-07T17:35:00Z"
  }
]
```

---

### `GET /reviews/{review_id}`
Returns details for a single review case including conflicting fact references and evidence snippets.

---

### `POST /reviews/{review_id}/resolve`
Submits a clinical reviewer's decision to resolve ambiguity or conflict.

**Request Body:**
```json
{
  "decision": "approve_a",
  "resolution_notes": "Confirmed with Dr. Sharma's clinic that Oct 14 is correct follow-up date.",
  "winning_fact_id": "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "reviewer_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f"
}
```

Allowed Decisions:
- `approve_a`: Accept Document A's claim, reject Document B's claim.
- `approve_b`: Accept Document B's claim, reject Document A's claim.
- `reject`: Reject both claims as invalid or unverified.
- `override`: Manually corrected fact by authorized clinician.

**Response `200 OK`:**
```json
{
  "id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "status": "RESOLVED",
  "decision": "approve_a",
  "resolution": "Confirmed with Dr. Sharma's clinic that Oct 14 is correct follow-up date.",
  "resolved_by": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "resolved_at": "2026-10-07T17:40:00Z"
}
```
