# CARELYNX — API Contracts

All endpoints use JSON unless otherwise stated.

Base path:

```text
/api/v1
```

## POST /documents

Upload a document.

Response:

```json
{
  "id": "uuid",
  "filename": "discharge-summary.pdf",
  "status": "UPLOADED"
}
```

---

## GET /documents/{document_id}

Returns document metadata and processing status.

---

## POST /documents/{document_id}/process

Starts processing.

Response:

```json
{
  "document_id": "uuid",
  "status": "PROCESSING"
}
```

---

## GET /cases/{case_id}/facts

Response:

```json
{
  "facts": [
    {
      "id": "uuid",
      "fact_type": "follow_up_date",
      "value": "2026-10-14",
      "status": "VERIFIED",
      "confidence": 0.98,
      "evidence": [
        {
          "document_id": "uuid",
          "page_number": 7,
          "section": "Follow-up",
          "snippet": "..."
        }
      ]
    }
  ]
}
```

---

## GET /facts/{fact_id}/evidence

Returns all source evidence.

---

## GET /cases/{case_id}/care-plan

Returns only validated/approved patient-facing content.

---

## POST /cases/{case_id}/translate

Request:

```json
{
  "language": "gu"
}
```

Allowed MVP languages:

```text
en
hi
gu
```

---

## GET /reviews

Returns review cases accessible to reviewer.

---

## GET /reviews/{review_id}

Returns:
- reason
- evidence
- conflicting values
- current system status

---

## POST /reviews/{review_id}/resolve

Request:

```json
{
  "decision": "APPROVE_SOURCE_A",
  "reason": "Verified against original document."
}
```

Possible decisions must be explicitly modeled, not arbitrary strings.

---

## Error Contract

All API errors:

```json
{
  "error": {
    "code": "REVIEW_REQUIRED",
    "message": "Human verification is required for this information.",
    "request_id": "uuid"
  }
}
```

Never return stack traces to clients.
