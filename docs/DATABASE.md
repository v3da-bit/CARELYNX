# CARELYNX — Database Specification

Use PostgreSQL.

All primary keys are UUID.

All timestamps are UTC.

## patients

```sql
id UUID PRIMARY KEY
preferred_language VARCHAR(10)
external_reference TEXT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Avoid storing unnecessary identity data in MVP.

---

## cases

```sql
id UUID PRIMARY KEY
patient_id UUID NOT NULL
status VARCHAR(32) NOT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

---

## documents

```sql
id UUID PRIMARY KEY
case_id UUID NOT NULL
filename TEXT NOT NULL
mime_type VARCHAR(100) NOT NULL
storage_key TEXT NOT NULL
page_count INTEGER NULL
processing_status VARCHAR(32) NOT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

---

## document_pages

```sql
id UUID PRIMARY KEY
document_id UUID NOT NULL
page_number INTEGER NOT NULL
text TEXT
ocr_confidence NUMERIC(5,4) NULL
created_at TIMESTAMPTZ NOT NULL
```

Unique:

```text
(document_id, page_number)
```

---

## facts

```sql
id UUID PRIMARY KEY
case_id UUID NOT NULL
fact_type VARCHAR(100) NOT NULL
value JSONB NOT NULL
status VARCHAR(32) NOT NULL
confidence NUMERIC(5,4) NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

---

## evidence

```sql
id UUID PRIMARY KEY
fact_id UUID NOT NULL
document_id UUID NOT NULL
page_number INTEGER NOT NULL
section TEXT NULL
snippet TEXT NULL
created_at TIMESTAMPTZ NOT NULL
```

---

## conflicts

```sql
id UUID PRIMARY KEY
case_id UUID NOT NULL
fact_type VARCHAR(100) NOT NULL
conflict_data JSONB NOT NULL
status VARCHAR(32) NOT NULL
created_at TIMESTAMPTZ NOT NULL
resolved_at TIMESTAMPTZ NULL
```

---

## review_cases

```sql
id UUID PRIMARY KEY
case_id UUID NOT NULL
reason TEXT NOT NULL
severity VARCHAR(32) NOT NULL
status VARCHAR(32) NOT NULL
assigned_to UUID NULL
resolution TEXT NULL
created_at TIMESTAMPTZ NOT NULL
resolved_at TIMESTAMPTZ NULL
```

---

## audit_logs

```sql
id UUID PRIMARY KEY
case_id UUID NULL
actor_type VARCHAR(32) NOT NULL
actor_id UUID NULL
event_type VARCHAR(100) NOT NULL
metadata JSONB NOT NULL DEFAULT '{}'
created_at TIMESTAMPTZ NOT NULL
```

Never put full patient documents or secrets into audit metadata.
