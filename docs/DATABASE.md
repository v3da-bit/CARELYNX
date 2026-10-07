# CARELYNX — Database Specification

> **Document Version:** 1.1.0  
> **Source of Truth:** `/docs/DATABASE.md`  
> **Target RDBMS:** PostgreSQL (Production) / SQLite (Local Dev & Unit Tests)  
> **ORM Layer:** SQLAlchemy 2.0 + Alembic Migrations  

---

## 1. Global Schema Invariants

1. **Primary Keys:** Every table uses UUIDv4 (`UUID` type in PostgreSQL, mapped as 36-char string or native UUID in SQLite).
2. **Timestamps:** All timestamps are timezone-aware UTC (`TIMESTAMPTZ` in Postgres, ISO 8601 strings in SQLite).
3. **JSON Storage:** Structured clinical payloads, conflict trees, and audit metadata are stored in `JSONB` on Postgres and standard `JSON` on SQLite.
4. **Referential Integrity:** Foreign keys enforce `ON DELETE CASCADE` on case-owned child records (documents, facts, review cases).

---

## 2. Table Specifications

### 2.1 `patients`
Stores patient profiles and preferred communication language.

```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    external_reference TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

---

### 2.2 `cases`
Encounter container grouping all documents, extracted facts, and review items for a specific discharge event.

```sql
CREATE TABLE cases (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_cases_patient_id ON cases(patient_id);
```

---

### 2.3 `documents`
Metadata and processing state for uploaded discharge summaries, prescriptions, or lab reports.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    storage_key TEXT NOT NULL,
    page_count INTEGER NULL,
    processing_status VARCHAR(32) NOT NULL DEFAULT 'UPLOADED',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    sha256 VARCHAR(64) NOT NULL DEFAULT '',
    document_kind VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
    error_code VARCHAR(64) NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_documents_case_id ON documents(case_id);
```

---

### 2.4 `document_pages`
Stores segmented page text, OCR confidence scores, and heuristic quality evaluations.

```sql
CREATE TABLE document_pages (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NULL,
    ocr_confidence NUMERIC(5,4) NULL,
    extraction_method VARCHAR(32) NOT NULL,
    text_quality NUMERIC(5,4) NULL,
    quality_flags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_document_pages_doc_page UNIQUE (document_id, page_number)
);
CREATE INDEX ix_document_pages_document_id ON document_pages(document_id);
```

---

### 2.5 `facts`
Structured candidate facts extracted from clinical documentation.

```sql
CREATE TABLE facts (
    id UUID PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    fact_type VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    status VARCHAR(32) NOT NULL,
    confidence NUMERIC(5,4) NULL,
    status_reasons JSONB NOT NULL DEFAULT '[]',
    extracted_by VARCHAR(100) NOT NULL DEFAULT '',
    human_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_facts_case_id ON facts(case_id);
```

Allowed `fact_type`:
- `follow_up_date`
- `instruction`
- `medication`
- `warning`

Allowed `status`:
- `VERIFIED`
- `NEEDS_REVIEW`
- `HUMAN_REQUIRED`
- `CONFLICT_DETECTED`
- `REJECTED`

---

### 2.6 `evidence`
Line-by-line evidence citations linking each fact to its source document page and verbatim text excerpt.

```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY,
    fact_id UUID NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    section TEXT NULL,
    snippet TEXT NULL,
    char_start INTEGER NULL,
    char_end INTEGER NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_evidence_fact_id ON evidence(fact_id);
CREATE INDEX ix_evidence_document_id ON evidence(document_id);
```

---

### 2.7 `conflicts`
Records contradictory values detected across documents belonging to the same case.

```sql
CREATE TABLE conflicts (
    id UUID PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    fact_type VARCHAR(100) NOT NULL,
    conflict_data JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ NULL
);
CREATE INDEX ix_conflicts_case_id ON conflicts(case_id);
```

---

### 2.8 `review_cases`
Actionable review tickets for clinical reviewers to inspect and resolve ambiguous or conflicting facts.

```sql
CREATE TABLE review_cases (
    id UUID PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    reason_code VARCHAR(32) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    assigned_to UUID NULL,
    resolution TEXT NULL,
    fact_ids JSONB NOT NULL DEFAULT '[]',
    conflict_id UUID REFERENCES conflicts(id) ON DELETE SET NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    recommended_action TEXT NOT NULL DEFAULT '',
    decision VARCHAR(32) NULL,
    resolved_by VARCHAR(100) NULL,
    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ NULL
);
CREATE INDEX ix_review_cases_case_id ON review_cases(case_id);
```

---

### 2.9 `audit_logs`
Immutable audit trail capturing all document processing, safety blocks, and reviewer decisions.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    case_id UUID NULL,
    actor_type VARCHAR(32) NOT NULL,
    actor_id UUID NULL,
    event_type VARCHAR(100) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_audit_logs_case_id ON audit_logs(case_id);
```

---

## 3. Database Migrations & Tooling

Alembic manages migrations under `apps/api/alembic/`.
To execute migrations against the configured database:

```bash
cd apps/api
source .venv/bin/activate
alembic upgrade head
```
