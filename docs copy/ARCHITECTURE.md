# CARELYNX — System Architecture

## 1. Architecture Goal

Build a modular, evidence-first healthcare document processing platform where AI assists with extraction and communication but does not autonomously make clinical decisions.

---

## 2. High-Level Architecture

```text
                    ┌─────────────────────┐
                    │   Next.js Frontend  │
                    │ Patient / Reviewer  │
                    └──────────┬──────────┘
                               │ HTTPS
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI API     │
                    └──────────┬──────────┘
                               │
       ┌───────────────────────┼────────────────────────┐
       ▼                       ▼                        ▼
 Document Service        Patient/Case Service     Review Service
       │                       │                        │
       ▼                       ▼                        ▼
 Storage                 PostgreSQL              Review Queue
       │
       ▼
 Processing Pipeline
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
OCR  Parser      Document Classifier
 └─────┬─────────────┘
       ▼
 Structured Extraction
       │
       ▼
 Evidence Engine
       │
       ├──────────────┐
       ▼              ▼
 Safety Engine    Translation Engine
       │              │
       └──────┬───────┘
              ▼
         Care Plan
              │
              ▼
       Human Review if needed
```

---

## 3. Major Components

### 3.1 Frontend
Responsibilities:
- Upload
- Processing status
- Care plan
- Evidence viewer
- Translation
- Review UI

Suggested:
- Next.js
- TypeScript
- Tailwind CSS
- Accessible component system

### 3.2 API
Responsibilities:
- Authentication
- Authorization
- Workflow orchestration
- Input validation
- API contracts

Suggested:
- FastAPI
- Pydantic
- Python

### 3.3 Document Service
Responsibilities:
- Upload validation
- File metadata
- Storage
- Retrieval

### 3.4 Processing Pipeline
Responsibilities:
- OCR
- Text extraction
- Page segmentation
- Document classification
- Structured extraction

### 3.5 Evidence Engine
Responsibilities:
- Map extracted facts to source pages/sections.
- Reject unsupported claims.
- Maintain evidence relationships.

### 3.6 Safety Engine
Responsibilities:
- Validate generated output.
- Detect unsupported claims.
- Detect conflicts.
- Determine review status.
- Enforce abstention.

### 3.7 Translation Engine
Responsibilities:
- Translate validated patient-facing information.
- Preserve source meaning and uncertainty.
- Never introduce new medical advice.

### 3.8 Review Service
Responsibilities:
- Create review cases.
- Assign reviewer.
- Record decision.
- Preserve audit trail.

---

## 4. AI Architecture

AI must be behind an abstraction:

```text
InferenceProvider
       │
 ┌─────┴─────────────┐
 ▼                   ▼
AMD/ROCm Provider   Local/Other Provider
```

The application should not directly depend on a specific model vendor.

Suggested flow:

```text
Source Document
      ↓
OCR/Text
      ↓
LLM structured extraction
      ↓
Schema validation
      ↓
Evidence validation
      ↓
Safety validation
      ↓
Persist
```

The LLM is not the final authority.

---

## 5. AMD Integration

AMD is used for meaningful AI inference workload.

Target deployment:

```text
CARELYNX AI Service
        ↓
Inference Runtime
        ↓
AMD GPU / ROCm
        ↓
Model
```

Potential inference stack:
- PyTorch
- vLLM
- ONNX Runtime
- Other ROCm-compatible runtime

The selected stack should be validated against the actual AMD hardware/environment available for the hackathon.

---

## 6. Database Schema

### patients

```text
id UUID PK
external_reference TEXT NULL
preferred_language TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
```

### cases

```text
id UUID PK
patient_id UUID FK
status TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
```

### documents

```text
id UUID PK
case_id UUID FK
filename TEXT
mime_type TEXT
storage_key TEXT
page_count INT
processing_status TEXT
created_at TIMESTAMP
```

### document_pages

```text
id UUID PK
document_id UUID FK
page_number INT
text TEXT
ocr_confidence NUMERIC NULL
created_at TIMESTAMP
```

### facts

```text
id UUID PK
case_id UUID FK
fact_type TEXT
value JSONB
status TEXT
confidence NUMERIC
created_at TIMESTAMP
updated_at TIMESTAMP
```

### evidence

```text
id UUID PK
fact_id UUID FK
document_id UUID FK
page_number INT
section TEXT NULL
snippet TEXT NULL
created_at TIMESTAMP
```

### conflicts

```text
id UUID PK
case_id UUID FK
fact_type TEXT
conflict_data JSONB
status TEXT
created_at TIMESTAMP
resolved_at TIMESTAMP NULL
```

### review_cases

```text
id UUID PK
case_id UUID FK
reason TEXT
severity TEXT
status TEXT
assigned_to UUID NULL
resolution TEXT NULL
created_at TIMESTAMP
resolved_at TIMESTAMP NULL
```

### audit_logs

```text
id UUID PK
case_id UUID NULL
actor_type TEXT
actor_id UUID NULL
event_type TEXT
metadata JSONB
created_at TIMESTAMP
```

---

## 7. Data Flow

```text
1. User uploads document
2. API validates file
3. Document stored
4. Processing job created
5. OCR/text extraction runs
6. Text is segmented by page
7. AI extracts structured facts
8. Schema validator checks output
9. Evidence engine links facts to source
10. Safety engine checks ambiguity/conflicts
11. Review cases created when needed
12. Care plan generated from validated facts
13. Translation occurs on validated content
14. Patient/reviewer sees result
15. Audit event recorded
```

---

## 8. Security Architecture

### Authentication
Use secure session/token management.

### Authorization
Role-based access:

```text
PATIENT
CAREGIVER
REVIEWER
ADMIN
```

### Storage
- Encrypt sensitive data at rest.
- Encrypt traffic in transit.
- Restrict document access by case/user.

### Secrets
All secrets belong in environment variables or secret management.

### Logging
Never log:
- Passwords
- API keys
- Full documents
- Unnecessary patient identifiers

---

## 9. Safety Architecture

```text
             Generated Candidate
                     │
                     ▼
              Schema Validator
                     │
                     ▼
              Evidence Checker
                     │
             ┌───────┴────────┐
             ▼                ▼
          Supported        Unsupported
             │                │
             ▼                ▼
       Safety Checker       BLOCK
             │
       ┌─────┴─────┐
       ▼           ▼
     Safe        Uncertain
       │           │
       ▼           ▼
    Publish     Human Review
```

### Golden rule

> **No evidence → no definitive claim.**

---

## 10. Observability

Track:
- Processing duration
- OCR errors
- Extraction errors
- Evidence failures
- Review triggers
- Review resolution time
- Unsupported claim blocks
- Document conflicts
- Model latency
- Inference provider
- Token/resource metrics where available

---

## 11. Deployment

Suggested MVP:

```text
Frontend
  ↓
Next.js deployment

Backend
  ↓
FastAPI

Database
  ↓
Supabase PostgreSQL

Object Storage
  ↓
Supabase Storage / compatible object storage

AI
  ↓
AMD ROCm inference service
```

For production, separate:
- Web tier
- API tier
- Worker tier
- AI inference tier
- Database
- Object storage
- Observability

---

## 12. Future Architecture

```text
                    CARELYNX PLATFORM
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
 Patient Journey      Staff Copilot       Integrations
       │                   │                   │
       ▼                   ▼                   ▼
 Documents            Review Queue         Hospital Systems
 Appointment          Workflow             FHIR/HL7
 Intake               Analytics            Scheduling
 Discharge
       │
       ▼
 Evidence Graph
       │
       ▼
 Safety + Human Oversight
       │
       ▼
 AMD Accelerated AI
```
